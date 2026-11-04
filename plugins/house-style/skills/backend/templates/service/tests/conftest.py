"""Shared fixtures: an in-memory SQLite database standing in for the service's Postgres.

The model imports exist for their side effect: they register tables on ``SQLModel.metadata``
before ``create_all`` runs, so dropping one drops its table from the test schema.
"""

import pytest
from fastapi import FastAPI
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from {{pkg}}.api.context import Principal
from {{pkg}}.api.deps.identity import require_user
from {{pkg}}.api.deps.session import get_session
from {{pkg}}.api.middleware.exception_handler import app_exception_handler
from {{pkg}}.api.routes import router
from {{pkg}}.lib.exceptions import {{App}}Exception
from {{pkg}}.models.note import Note

TEST_ORG_ID = "org_test_fixture"
TEST_USER_ID = "user_test_fixture"


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def user() -> Principal:
    return Principal(user_id=TEST_USER_ID, org_id=TEST_ORG_ID)


@pytest.fixture
def make_note(session):
    """Seed a note row directly, bypassing the service."""

    async def make(display_name: str = "Inbox", org_id: str = TEST_ORG_ID) -> Note:
        note = Note(org_id=org_id, display_name=display_name)
        session.add(note)
        await session.commit()
        return note

    return make


@pytest.fixture
async def client(session, user):
    """Drive the ``/v1`` surface on a freshly assembled app.

    ``main.app`` is not imported: its lifespan opens the real database. Only the session and the
    identity dependency are overridden.
    """
    app = FastAPI()
    app.add_exception_handler({{App}}Exception, app_exception_handler)
    app.include_router(router)
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[require_user] = lambda: user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://api") as http:
        yield http
