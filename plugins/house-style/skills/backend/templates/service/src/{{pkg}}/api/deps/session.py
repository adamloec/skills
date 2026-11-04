"""The database session dependency."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from {{pkg}}.config import db


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session, closed when the request ends."""
    async with db.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
