"""Note — the template's example resource, and the page shape its list route returns."""

from typing import ClassVar

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from {{pkg}}.lib.db import BaseModel


class Note(BaseModel, table=True):
    """A note owned by one organization."""

    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("org_id", "display_name", name="uq_notes_org_name"),)

    patchable: ClassVar[frozenset[str]] = frozenset({"display_name", "body", "is_pinned"})

    org_id: str = Field(index=True, description="Owning organization.")
    display_name: str = Field(description="Human label, unique within the organization.")
    body: str = Field(default="", description="Markdown content.")
    is_pinned: bool = Field(default=False, description="Pinned notes list first in the UI.")


class NotePage(PydanticBaseModel):
    """One page of notes, newest first."""

    items: list[Note]
    next_cursor: str | None = Field(
        default=None, description="Pass back as ``cursor`` for the next page. Null on the last.",
    )
