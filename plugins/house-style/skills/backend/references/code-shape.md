# Functions and classes

## Function shape

- **Primary inputs are positional. Scope and options are keyword-only after `*`.**
  ```python
  @staticmethod
  async def create(
      session: AsyncSession,
      *,
      org_id: str,
      display_name: str,
      description: str = "",
      created_by_user_id: str | None = None,
  ) -> Note:
  ```
- `session` is **always the first parameter** of a service method.
- **Guard clauses and early returns.** Validate, return or raise, then do the work. Don't nest
  `else` after a `return`.
  ```python
  async def delete(self, id: uuid.UUID) -> bool:
      """Delete a row, returning ``False`` when it did not exist."""
      obj = await self.get(id)
      if obj is None:
          return False
      await self.session.delete(obj)
      await self.session.commit()
      return True
  ```
- **A miss is `None` in a repository and an error in a service.** Use `get_or_404` where a miss
  is the caller's problem.
- **Re-raise with intent.** Use `from e` to keep a cause, and `from None` to hide internals
  from the wire.
  ```python
  except IntegrityError:
      await session.rollback()
      raise ConflictError(f"A note named '{display_name}' already exists") from None
  ```
- **No bare `except:`.** `except Exception` is allowed only at boundaries: the exception
  handler, the worker loop, plugin discovery.
- **Async by default for I/O.** Pure computation stays sync. Never block the event loop.
- **Default arguments are immutable.** Use `None` and build the value inside the function, or
  use `Field(default_factory=...)`.
- **Return concrete types:** `list[Model]`, not a generator, from repositories.
- **Keep functions small.** A median function is about 10 lines. When one grows a second job,
  extract it and give it a name and a docstring.

## Which kind of class

| Need | Use |
|---|---|
| Persisted row | `class X(BaseModel, table=True)` (UUID PK + timestamps). Use `TimestampMixin` for a string PK. Always set `__tablename__` |
| API payload / page / spec / non-table shape | pydantic `BaseModel` |
| Immutable value with behaviour, not serialized as an API model | `@dataclass(frozen=True, slots=True)` |
| Plugin base | `ABC` + `@abstractmethod`, named `Base<Kind>` |
| Narrow seam the code depends on | `Protocol` (`@runtime_checkable` when checked at runtime) |
| Settings | `pydantic_settings.BaseSettings` (see `config.md`) |
| Vocabulary | `StrEnum` |
| Stateless operations over a domain | service class of `@staticmethod`s |
| Data access on one session | repository instance |
| A connection or pool | infra client with `start()`/`stop()` (or `init()`/`close()`) |

Never use `TypedDict`. Never use `NamedTuple` for domain values; use a frozen dataclass.

## Table models

```python
class Note(BaseModel, table=True):
    """A note owned by one organization."""

    __tablename__ = "notes"
    __table_args__ = (UniqueConstraint("org_id", "display_name", name="uq_notes_org_name"),)

    patchable: ClassVar[frozenset[str]] = frozenset({"display_name", "body"})

    org_id: str = Field(index=True, description="Owning organization.")
    display_name: str = Field(description="Human label, unique within the organization.")
    body: str = Field(default="", description="Markdown content.")
    is_pinned: bool = Field(default=False, description="Pinned notes list first.")
```

- Mixins go first in the bases. `ClassVar`s declare behaviour (`patchable`, `permissions`).
- Secrets and internal fields use `Field(exclude=True)`. Derived values use `@computed_field`.
- Store enums as plain values with `sa_type=stored_by_value(Status)`, so adding a member needs
  no migration.
- **A value that is not a column:**
  - if it can be computed from the row, make it a `@computed_field`;
  - if it is a fact another entity owns, make it a column with exactly one writer;
  - if it is a volatile aggregate or a fact about the caller, give it its own endpoint.

## Services

```python
class NoteService:
    """Create, read, update and delete notes."""

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
```

- A service has one class per domain, no `__init__` and no state. Every method is
  `@staticmethod`.
- It builds repositories per call (`NoteRepository(session)`).
- It owns multi-row transactions: `flush()` → more writes → `commit()`.
- It raises only the app's typed errors.
- It reaches infrastructure through `config` singletons, never passed as parameters.

## Repositories

```python
class NoteRepository(BaseRepository[Note]):
    def __init__(self, session: AsyncSession):
        super().__init__(Note, session)

    async def get_for_org(self, org_id: str, note_id: uuid.UUID) -> Note | None:
        """Load a note only if it belongs to the organization."""
        note = await self.session.get(Note, note_id)
        return note if note is not None and note.org_id == org_id else None
```

- The constructor is always those two lines. A repository class needs no class docstring.
- **Scoped reads take the owner id first**, so an unscoped read looks wrong at a glance. A
  cross-tenant id returns `None`, exactly like a missing one.
- Base writes (`create`, `update`, `delete`) commit and refresh. A domain method that is part of
  a larger unit says so: "The session is not committed."
- A race-safe get-or-create catches `IntegrityError`, rolls back and reads the row again
  (`ensure_*`).

## Infra clients

```python
class Storage:
    """S3-compatible object storage on one bucket."""

    def __init__(self, *, endpoint_url: str, bucket: str, access_key: str, secret_key: str):
        self._config = ...
        self._client = None

    async def start(self) -> None: ...
    async def stop(self) -> None: ...

    @property
    def client(self):
        """The live client, raising ``RuntimeError`` before ``start``."""
        if self._client is None:
            raise RuntimeError("Storage not started. Call start() first.")
        return self._client
```

- The constructor stores config and does **no I/O**.
- I/O happens in `start()` and `stop()`.
- They are constructed in `config.py` and started and stopped in the lifespan.

## Value objects and policies

- Frozen, slotted dataclasses for immutable context: `ForwardedScope`, `SecurityContext`,
  `Decision`.
- A request-scoped policy object (`Access(principal, session)`) is the one place that uses
  constructor injection. It memoizes lookups in `self._x` for one request and is injected as
  `AccessDep`.

## Enums

```python
class NoteStatus(StrEnum):
    """Where a note is in its lifecycle."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    @property
    def visible(self) -> bool:
        """Whether readers other than the author see the note."""
        return self is NoteStatus.PUBLISHED
```

Members are UPPER and values are lowercase. Predicates are `@property`s on the enum.

## Registries (plugin catalogs)

Use a registry when the app has a family of interchangeable implementations: providers,
integrations, components.

- Each kind has one process-global `Registry` in `registry.py`.
- A `@register_<kind>(type="…", name="…")` class decorator fills it at import time.
- The vertical's `__init__.py` imports the built-ins for their side effect.
- An optional vendor SDK registers only when `importlib.util.find_spec` finds it.
- `snapshot()` and `restore()` let tests swap in doubles.

## Properties and caching

- `@property` is for cheap derived reads only. Anything that does I/O is a method.
- `@cache` / `@lru_cache` sparingly, on pure functions of hashable input.
