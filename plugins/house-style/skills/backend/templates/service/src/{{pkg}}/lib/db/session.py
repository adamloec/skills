"""The async engine and session factory an app builds from its own settings."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class Database:
    """Async SQLAlchemy engine and session factory.

    Construction opens nothing. The owning app calls ``init`` at startup and ``close`` at
    shutdown; Alembic owns the schema, so neither creates tables.
    """

    def __init__(
        self,
        url: str,
        *,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout_seconds: int = 30,
        pool_recycle_seconds: int = 3600,
    ):
        self.engine = create_async_engine(
            url, echo=echo, pool_size=pool_size, max_overflow=max_overflow,
            pool_timeout=pool_timeout_seconds, pool_recycle=pool_recycle_seconds,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False,
        )

    async def init(self) -> None:
        """Open the first pooled connection, proving the database is reachable."""
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        """Dispose the engine and every pooled connection."""
        await self.engine.dispose()
