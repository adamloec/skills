# Tests

## Setup

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
markers = ["infra: requires local infrastructure (docker compose up -d)"]
addopts = "-m 'not infra'"
```

- With `asyncio_mode = "auto"`, a bare `async def test_…` runs. Don't decorate it.
- Every test directory has an empty `__init__.py`.
- A plain `uv run pytest` is **offline**. Tests that need live infrastructure carry
  `pytestmark = pytest.mark.infra` and run with `uv run pytest -m infra`.

## Layout

- Keep it flat to start: `tests/test_<resource or behaviour>.py`.
- Once a layer has several files of its own, mirror `src`: `tests/services/`,
  `tests/repositories/`, `tests/engine/`.
- Use `tests/live/` and `tests/e2e/` for suites that talk to a running stack. They skip
  themselves unless their env vars are set, and they refuse non-local hosts.

## Fixtures (`tests/conftest.py`)

```python
"""Shared fixtures: an in-memory SQLite database standing in for the service's Postgres.

The model imports exist for their side effect: they register tables on ``SQLModel.metadata``
before ``create_all`` runs.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from acme_api.models.note import Note  # noqa: F401

TEST_ORG_ID = "org_test_fixture"


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
def make_note(session):
    """Seed a note row directly, bypassing the service."""

    async def _make(display_name: str = "Inbox", org_id: str = TEST_ORG_ID) -> Note:
        note = Note(org_id=org_id, display_name=display_name)
        session.add(note)
        await session.commit()
        return note

    return _make
```

- `engine` and `session` are fixtures on in-memory `sqlite+aiosqlite://`. Recreate any
  Postgres-only partial indexes natively in `engine`.
- **Factories are fixtures returning an inner `async def _make(...)`.** Don't use factory_boy.
- **Almost no mocks.** Use the real repositories and services on SQLite. Use `monkeypatch` only
  for a true external boundary (vendor SDK, clock, network).
- Plain value fixtures are nouns: `org_id`, `user`.

## Two ways to test a route

**1. Call the handler directly** and pass deps as keyword arguments. This is fast and focuses
on behaviour:

```python
async def test_a_patch_with_an_unknown_field_is_refused(session, make_note):
    note = await make_note()
    with pytest.raises(BadRequestError, match="Cannot update owner"):
        await update_note(note_id=note.id, body={"owner": "x"}, user=USER, session=session)
```

**2. Drive the HTTP surface** through a **freshly assembled app**. Don't import `main.app`,
because its lifespan opens real infrastructure:

```python
@pytest.fixture
async def client(session):
    app = FastAPI()
    app.add_exception_handler(AcmeException, app_exception_handler)
    app.include_router(router)
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[require_user] = lambda: USER
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://api") as http:
        yield http


async def test_a_created_note_comes_back_with_its_name(client):
    response = await client.post("/v1/notes/", json={"display_name": "Inbox"})
    assert response.status_code == 201, response.text
    assert response.json()["display_name"] == "Inbox"
```

Override only the session and the identity or scope dependency.

## Style

- **Names are behaviour sentences:** `test_a_viewer_cannot_delete_a_note`,
  `test_a_cursor_resumes_after_the_last_row`.
- Use plain functions, not `class TestX:` groupings.
- Use `pytest.raises(XError, match="…")`. Put `response.text` in the status assert so a failure
  shows the body.
- Parametrize with `pytest.param(..., id="readable-case")`.
- Write one behaviour per test. A shared setup sequence goes in a fixture or a small `_helper`.
- A test file gets a docstring only when its setup is non-obvious.
