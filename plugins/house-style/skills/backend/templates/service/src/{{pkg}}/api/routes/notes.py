"""Note routes — CRUD over the caller's organization's notes.

Handlers check request shape and delegate to ``NoteService``.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Query

from {{pkg}}.api.deps.identity import UserDep
from {{pkg}}.api.deps.session import SessionDep
from {{pkg}}.models.note import Note, NotePage
from {{pkg}}.services.note_service import NoteService

router = APIRouter()


@router.get("/", response_model=NotePage)
async def list_notes(
    user: UserDep,
    session: SessionDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> NotePage:
    """List the organization's notes, newest first."""
    return await NoteService.list_page(session, org_id=user.org_id, cursor=cursor, limit=limit)


@router.get("/{note_id}", response_model=Note)
async def get_note(note_id: uuid.UUID, user: UserDep, session: SessionDep) -> Note:
    """Read one note.

    Raises:
        NotFoundError: No such note in the caller's organization.
    """
    return await NoteService.get(session, org_id=user.org_id, note_id=note_id)


@router.post("/", response_model=Note, status_code=201)
async def create_note(
    body: Annotated[dict, Body()], user: UserDep, session: SessionDep,
) -> Note:
    """Create a note in the caller's organization.

    Raises:
        BadRequestError: The body names a field that is not patchable, or the name is blank.
        ConflictError: A note with this name already exists.
    """
    return await NoteService.create(session, org_id=user.org_id, body=body)


@router.patch("/{note_id}", response_model=Note)
async def update_note(
    note_id: uuid.UUID, body: Annotated[dict, Body()], user: UserDep, session: SessionDep,
) -> Note:
    """Apply a partial update to a note.

    Raises:
        BadRequestError: The body names a field that is not patchable, or the name is blank.
        ConflictError: The new name is already taken.
        NotFoundError: No such note in the caller's organization.
    """
    return await NoteService.update(session, org_id=user.org_id, note_id=note_id, body=body)


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: uuid.UUID, user: UserDep, session: SessionDep) -> None:
    """Delete a note.

    Raises:
        NotFoundError: No such note in the caller's organization.
    """
    await NoteService.delete(session, org_id=user.org_id, note_id=note_id)
