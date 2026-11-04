"""NoteService — note lifecycle within one organization.

Every method takes the request's session and raises typed exceptions the API layer maps to
status codes; request-shape checks stay at the route.
"""

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from {{pkg}}.lib.exceptions import BadRequestError, ConflictError, NotFoundError
from {{pkg}}.lib.utils.logger import get_logger
from {{pkg}}.lib.utils.time import utcnow
from {{pkg}}.models.note import Note, NotePage
from {{pkg}}.repositories.note_repository import NoteRepository

logger = get_logger("services.notes")


class NoteService:
    """Create, read, update and delete notes."""

    @staticmethod
    async def list_page(
        session: AsyncSession, *, org_id: str, cursor: str | None, limit: int,
    ) -> NotePage:
        """List the organization's notes, newest first."""
        items, next_cursor = await NoteRepository(session).list_page(
            org_id, cursor=cursor, limit=limit,
        )
        return NotePage(items=items, next_cursor=next_cursor)

    @staticmethod
    async def get(session: AsyncSession, *, org_id: str, note_id: uuid.UUID) -> Note:
        """Load one of the organization's notes.

        Raises:
            NotFoundError: No such note in this organization.
        """
        note = await NoteRepository(session).get_for_org(org_id, note_id)
        if note is None:
            raise NotFoundError("Note not found")
        return note

    @staticmethod
    async def create(session: AsyncSession, *, org_id: str, body: Mapping[str, Any]) -> Note:
        """Create a note from a create body.

        Raises:
            BadRequestError: A field is not patchable, or the name is missing or blank.
            ConflictError: The organization already has a note with this name.
        """
        fields = _validated_fields(body, require_name=True)
        note = Note(org_id=org_id, **fields)
        try:
            note = await NoteRepository(session).create(note)
        except IntegrityError:
            await session.rollback()
            raise ConflictError(f"A note named '{fields['display_name']}' already exists") from None
        logger.info("Note created", note_id=str(note.id), org_id=org_id)
        return note

    @staticmethod
    async def update(
        session: AsyncSession, *, org_id: str, note_id: uuid.UUID, body: Mapping[str, Any],
    ) -> Note:
        """Apply a partial update to one of the organization's notes.

        Raises:
            BadRequestError: A field is not patchable, or the new name is blank.
            ConflictError: The new name is already taken in this organization.
            NotFoundError: No such note in this organization.
        """
        fields = _validated_fields(body, require_name=False)
        note = await NoteService.get(session, org_id=org_id, note_id=note_id)
        for name, value in fields.items():
            setattr(note, name, value)
        note.updated_at = utcnow()
        try:
            return await NoteRepository(session).update(note)
        except IntegrityError:
            await session.rollback()
            raise ConflictError(f"A note named '{note.display_name}' already exists") from None

    @staticmethod
    async def delete(session: AsyncSession, *, org_id: str, note_id: uuid.UUID) -> None:
        """Delete one of the organization's notes.

        Raises:
            NotFoundError: No such note in this organization.
        """
        note = await NoteService.get(session, org_id=org_id, note_id=note_id)
        await session.delete(note)
        await session.commit()
        logger.info("Note deleted", note_id=str(note_id), org_id=org_id)


def _validated_fields(body: Mapping[str, Any], *, require_name: bool) -> dict[str, Any]:
    """Validate a create or patch body, trimming the name and refusing a blank one.

    Raises:
        BadRequestError: A field is not patchable, or the name is blank, or missing when
            ``require_name`` is set.
    """
    fields = Note.validate_patch(body)
    if "display_name" in fields:
        fields["display_name"] = fields["display_name"].strip()
    if (require_name or "display_name" in fields) and not fields.get("display_name"):
        raise BadRequestError("Note name is required")
    return fields
