"""DB primitives: the shared SQLModel bases and the generic repository."""

import base64
import uuid
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, select

from {{pkg}}.lib.exceptions import BadRequestError, NotFoundError
from {{pkg}}.lib.utils.time import UTCDateTime, ensure_utc, utcnow


def stored_by_value(enum: type[StrEnum]) -> SAEnum:
    """Build a column type that stores a ``StrEnum`` as its plain value, with no database enum.

    Adding a member then needs no migration, and a loaded row holds the member rather than a
    bare string.
    """
    return SAEnum(
        enum, native_enum=False, length=64, values_callable=lambda e: [m.value for m in e],
    )


class TimestampMixin(SQLModel):
    """Creation and update timestamps, and the strict partial update every table shares."""

    created_at: UTCDateTime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))
    updated_at: UTCDateTime = Field(default_factory=utcnow, sa_type=DateTime(timezone=True))

    patchable: ClassVar[frozenset[str]] = frozenset()
    """The fields a partial update may change. Every other field is the server's to set."""

    @classmethod
    def validate_patch(cls, body: Mapping[str, Any]) -> dict[str, Any]:
        """Check a partial update's body against this model, without applying it.

        Every key must name a patchable field, so a misspelled or server-owned field is refused
        rather than silently dropped, and every value is validated as its field's type.

        Returns:
            The body's values, validated.

        Raises:
            BadRequestError: A key names no patchable field, or a value does not fit its field.
        """
        unknown = sorted(set(body) - cls.patchable)
        if unknown:
            raise BadRequestError(f"Cannot update {', '.join(unknown)} on {cls.__name__}")
        try:
            return {
                name: TypeAdapter(cls.model_fields[name].annotation).validate_python(value)
                for name, value in body.items()
            }
        except ValidationError as e:
            raise BadRequestError(str(e)) from e

    def patch(self, body: Mapping[str, Any]) -> dict[str, Any]:
        """Apply a partial update's body to this row, after ``validate_patch`` checks it.

        Returns:
            The fields it changed, with their new values.
        """
        changes = self.validate_patch(body)
        for name, value in changes.items():
            setattr(self, name, value)
        if changes:
            self.updated_at = utcnow()
        return changes


class BaseModel(TimestampMixin):
    """A timestamped row keyed by a generated UUID."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """CRUD over one model on a caller-owned session.

    Every write commits and refreshes, so the caller holds a live instance afterwards.
    """

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID) -> T | None:
        """Load a row, or ``None`` when it is missing."""
        return await self.session.get(self.model, id)

    async def get_or_404(self, id: uuid.UUID, label: str | None = None) -> T:
        """Load a row, raising ``NotFoundError`` when it is missing.

        Args:
            id: Primary key to load.
            label: What to call the row in the error. Defaults to the model's class name.

        Raises:
            NotFoundError: No row has this key.
        """
        obj = await self.session.get(self.model, id)
        if obj is None:
            raise NotFoundError(f"{label or self.model.__name__} not found")
        return obj

    async def list(self, offset: int = 0, limit: int = 100) -> list[T]:
        """List rows by offset. Only for small, bounded tables; growing ones page by cursor."""
        result = await self.session.execute(select(self.model).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def create(self, obj: T) -> T:
        """Insert a row and commit."""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        """Persist a modified row and commit."""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a row and commit, returning ``False`` when it did not exist."""
        obj = await self.get(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True

    @staticmethod
    def encode_cursor(at: datetime, id: uuid.UUID) -> str:
        """Pack a row's ``(created_at, id)`` sort key into an opaque page cursor."""
        raw = f"{ensure_utc(at).isoformat()}|{id}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    @staticmethod
    def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
        """Unpack a cursor made by ``encode_cursor``.

        Raises:
            BadRequestError: The cursor was not issued by ``encode_cursor``.
        """
        try:
            at, id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
            return datetime.fromisoformat(at), uuid.UUID(id)
        except ValueError:
            raise BadRequestError("Invalid page cursor") from None
