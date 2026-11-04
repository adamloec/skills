"""Alembic environment for the service's own database.

Autogenerate is filtered to the tables this service owns, so a model imported from elsewhere is
never created or dropped here. Migrations run under a Postgres transaction-level advisory lock,
so concurrent boots serialize: whoever wins migrates, the rest block, then see ``head`` and
no-op. The URL comes from ``CoreSettings`` directly rather than from ``config.py``, so running a
migration constructs no application singletons.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from {{pkg}}.lib.config import CoreSettings
from {{pkg}}.models.note import Note

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

core = CoreSettings()
target_metadata = SQLModel.metadata

OWNED_TABLES = frozenset({Note.__tablename__})
"""The tables this service owns — the only ones autogenerate may touch."""

LOCK_KEY = 4_100_000_001
"""This service's advisory-lock key. Unique per service, since locks are instance-wide."""


def include_name(name, type_, parent_names) -> bool:
    """Filter names read back from the database to the owned tables."""
    return name in OWNED_TABLES if type_ == "table" else True


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    """Filter metadata-side objects to the owned tables, so a foreign model is never created."""
    return name in OWNED_TABLES if type_ == "table" else True


def run_migrations_locked(connection: Connection) -> None:
    """Run every pending migration on one connection, holding this service's advisory lock."""
    context.configure(
        connection=connection, target_metadata=target_metadata, include_name=include_name,
        include_object=include_object, compare_type=True, compare_server_default=True,
    )
    with context.begin_transaction():
        connection.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": LOCK_KEY})
        context.run_migrations()


async def run_migrations_online() -> None:
    """Migrate against the live database."""
    engine = create_async_engine(core.database_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations_locked)
    await engine.dispose()


def run_migrations_offline() -> None:
    """Emit the migration SQL without connecting."""
    context.configure(
        url=core.database_url, target_metadata=target_metadata, include_name=include_name,
        include_object=include_object, literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
