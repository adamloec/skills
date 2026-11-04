# API (FastAPI)

## `main.py`

```python
"""Ledger API — FastAPI entrypoint.

Owns the ledger's tables and serves them under ``/v1``.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from ledger_api.api.middleware.exception_handler import (
    app_exception_handler,
    unhandled_exception_handler,
)
from ledger_api.api.routes import router
from ledger_api.config import db
from ledger_api.lib.exceptions import LedgerException
from ledger_api.lib.utils.logger import get_logger

logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the database engine, and close it on shutdown.

    No schema is created here. Alembic owns it, and the image entrypoint has already applied it.
    """
    logger.info("Starting Ledger API")
    await db.init()
    logger.info("Ledger API started")
    try:
        yield
    finally:
        logger.info("Shutting down Ledger API")
        await db.close()
        logger.info("Ledger API stopped")


app = FastAPI(title="Ledger API", version="0.1.0", lifespan=lifespan)

app.add_exception_handler(LedgerException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(router)


@app.get("/health", status_code=204)
async def health() -> None:
    """Report liveness: the process is up."""


@app.get("/readiness", status_code=204)
async def readiness() -> None:
    """Report readiness: the database is reachable.

    Raises:
        HTTPException: 503 when the database cannot be queried.
    """
    try:
        async with db.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable") from None
```

- Use a **module-level `app` object**, not an app factory.
- Register two exception handlers: the app's exception root goes to the envelope, and
  `Exception` goes to an opaque 500.
- Add middleware next, then **one** `include_router(router)`.
- `/health` returns 204 with no I/O. `/readiness` returns 204, or 503 when a hard dependency is
  down. Both live on the app, outside `/v1`.
- **Lifespan:** log, then start each singleton in dependency order. Wrap `yield` in
  `try/finally`, stop in reverse order, and log each phase ("Starting X", "X started",
  "Shutting down X", "X stopped").
- Run it with `uv run uvicorn <pkg>.main:app --reload --port <port>`.

## Router assembly: `api/routes/__init__.py`

```python
"""The ``/v1`` router — every route, and which callers may reach it.

Coarse access is drawn here, at mount time, rather than route by route.
"""

from fastapi import APIRouter, Depends

from ledger_api.api.deps.identity import require_user
from ledger_api.api.routes import invoices, me, notes

router = APIRouter(prefix="/v1")

AUTHENTICATED = [Depends(require_user)]

router.include_router(me.router, prefix="/me", tags=["me"])
router.include_router(
    invoices.router, prefix="/invoices", tags=["invoices"], dependencies=AUTHENTICATED,
)
router.include_router(notes.router, prefix="/notes", tags=["notes"], dependencies=AUTHENTICATED)
```

- Route modules are imported alphabetically in one import.
- Each module is mounted with `prefix="/<plural-kebab>"` and `tags=["<same>"]`.
- **Security boundaries go on the mount** (`dependencies=[...]`), never repeated on each route.
  Name the dependency lists in UPPER_SNAKE.
- A route module may gate all its routes with `APIRouter(dependencies=[Depends(load_context)])`.

## Route handlers

```python
@router.get("/", response_model=NotePage)
async def list_notes(
    user: UserDep,
    session: SessionDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> NotePage:
    """List the caller's notes, newest first."""
    return await NoteService.list_page(session, org_id=user.org_id, cursor=cursor, limit=limit)


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
        BadRequestError: The body names a field that is not patchable.
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
```

**Rules:**

- Set `response_model=` **and** the matching return annotation.
- Status codes: `status_code=201` on create. `status_code=204` with `-> None` on delete and on
  commands that return nothing.
- Paths: collections use `"/"` with the trailing slash, items use `"/{<entity>_id}"`, and
  sub-resources and commands use `"/{<entity>_id}/<noun-or-verb>"`.
- Path ids are typed `uuid.UUID`. A public prefixed id is a `str` and is parsed explicitly.
- **Parameter order:** path params, then body, then deps (identity, access, session), then
  query params with defaults.
- Query params are `x: T | None = Query(default=None)`. Paging is
  `limit: int = Query(default=50, ge=1, le=200)` with `cursor: str | None`.
- **Creates and partial updates** take `body: Annotated[dict, Body()]` and go through
  `Model.validate_patch(body)` / `row.patch(body)`. Unknown keys get a 400 that names them. The
  service checks required fields. No `*Update` model exists. A typed `<Entity>Create` body
  exists only when the create shape is structurally different from the entity, e.g. it
  carries a secret that is never read back.
- A one-field command uses `Annotated[str, Body(embed=True)]`. A multi-field command gets a
  typed `<Verb><Noun>Request` model, never a `dict` read with `.get`.
- **Thin handlers.** A handler checks request shape and authorization, then delegates to one
  service call. Business rules live in the service.
- `HTTPException` is for transport and request-shape problems at the edge only. Everything else
  raises typed errors.

## Dependencies: `api/deps/`

```python
async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session, closed when the request ends."""
    async with db.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

- Each provider is followed **immediately** by its `<Thing>Dep` alias. Handlers use the alias,
  never a raw `Depends(...)` in the signature, except for a parameterized gate.
- Gates are `require_<condition>`. They raise, or return the principal. A parameterized gate
  is a factory:
  ```python
  def require_permission(permission: str) -> Callable[..., Principal]:
      """Gate a route on one permission in the caller's active scope."""

      async def gate(user: UserDep, access: AccessDep) -> Principal:
          await access.authorize(permission)
          return user

      return gate
  ```
- **Authorization that needs the row is imperative after load.** It is done by a
  request-scoped policy object (`AccessDep`) that memoizes lookups:
  `access.authorize(Action.WRITE, note)`. Coarse "is signed in / has role" gates go on the mount.

## Middleware

- Subclass `BaseHTTPMiddleware` and implement `dispatch`. Name the class `<Thing>Middleware`.
- **Fail closed:**
  - An unset secret answers 503 on every path except the open ones.
  - A caller who cannot prove itself gets a plain 404, which reveals nothing.
  - Open paths are an explicit `OPEN_PATHS = frozenset({"/health", "/readiness"})`.
- Strip inbound copies of any header the middleware itself asserts, so a client can never forge
  its own scope.

## Pagination

Use keyset pagination on any table that grows:

- Order by `created_at DESC, id DESC`. That order is total, so the cursor is unambiguous.
- Fetch `limit + 1` rows. The extra row only tells you whether another page exists.
- Return `<Entity>Page(items=[...], next_cursor=...)`. The cursor is opaque base64 of
  `(created_at, id)`, and `None` means the last page.
- `offset`/`limit` is only for small, bounded admin lists.

## Errors on the wire

Every typed error serializes to one envelope:

```json
{"type": "ledger_error", "code": "not_found", "message": "Note not found",
 "context": {}, "hint": null, "is_retryable": false}
```

The HTTP status rides on the exception class and is never in the body. FastAPI's own 422
validation errors stay as FastAPI renders them. See `errors-and-logging.md`.

## Calling a sibling service

- Use one client module, `<sibling>_client.py`, and one `request()` seam.
- It attaches the internal secret and forwarded scope headers, and maps transport failures and
  5xx responses to `UpstreamError` (502, retryable).
- It returns decoded JSON, or `None` on 204.
- It uses the shared `HttpPool` from `config.py`.
