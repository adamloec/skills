"""NoteRepository — organization-scoped note lookups and the keyset page."""

import uuid

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from {{pkg}}.lib.db import BaseRepository
from {{pkg}}.models.note import Note


class NoteRepository(BaseRepository[Note]):
    def __init__(self, session: AsyncSession):
        super().__init__(Note, session)

    async def get_for_org(self, org_id: str, note_id: uuid.UUID) -> Note | None:
        """Load a note only if it belongs to the organization; another org's id is a miss."""
        note = await self.session.get(Note, note_id)
        return note if note is not None and note.org_id == org_id else None

    async def list_page(
        self, org_id: str, *, cursor: str | None, limit: int,
    ) -> tuple[list[Note], str | None]:
        """List the organization's notes newest first, one keyset page at a time.

        Returns:
            The page, and the cursor for the next one, or ``None`` on the last page.
        """
        stmt = select(Note).where(Note.org_id == org_id)
        if cursor:
            at, last_id = self.decode_cursor(cursor)
            stmt = stmt.where(
                or_(Note.created_at < at, and_(Note.created_at == at, Note.id < last_id)),
            )
        stmt = stmt.order_by(Note.created_at.desc(), Note.id.desc()).limit(limit + 1)
        rows = list((await self.session.execute(stmt)).scalars().all())
        page = rows[:limit]
        if len(rows) <= limit:
            return page, None
        return page, self.encode_cursor(page[-1].created_at, page[-1].id)
