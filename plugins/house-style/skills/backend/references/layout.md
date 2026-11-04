# Layout

## Repo top level

Every backend repo has the same top level:

```
src/<pkg>/          the code (src layout)
tests/              pytest suite
pyproject.toml      uv project; [dependency-groups] dev = [...]
uv.lock             committed
.python-version     3.13
README.md           what it owns, how to run it, configuration table
.github/workflows/ci.yml
```

A **service** repo adds:

```
Dockerfile
alembic.ini
migrations/{env.py, script.py.mako, versions/}
scripts/entrypoint.sh     migrate, then exec the process (see the infra skill)
```

The package name is the distribution name with underscores: `ledger-api` → `ledger_api`.

## Two package shapes

**Service: horizontal layers.** Use this for anything with an HTTP surface or a worker.

```
src/<pkg>/
  __init__.py            package docstring only
  main.py                FastAPI app + lifespan + /health + /readiness
  worker.py              second process entrypoint, if any: `python -m <pkg>.worker`
  config.py              settings + infra singletons
  <sibling>_client.py    outbound client to a sibling service (one seam, one file)
  api/
    __init__.py          empty
    context.py           frozen dataclasses for per-request trusted context (Principal)
    access.py            request-scoped authorization policy class, when there is one
    deps/
      __init__.py        """Request dependencies. Import from the specific submodule — there are no re-exports here."""
      session.py         get_session + SessionDep
      identity.py        require_user, UserDep …
    middleware/
      __init__.py        empty
      exception_handler.py
      <thing>_middleware.py
    routes/
      __init__.py        builds `router = APIRouter(prefix="/v1")`, mounts each module
      <resources>.py     one module per resource, plural noun
  services/              <domain>_service.py, one class each
  repositories/          <entity>_repository.py
  models/                <entity>.py, singular noun
  engine/                long-running or background execution, when the service has a worker
  lib/                   infrastructure primitives (see "Growing")
    config.py            CoreSettings: infra fields every process shares
    db/{__init__.py, base.py, session.py}
    exceptions/{__init__.py, base.py, http.py, serialization.py}
    utils/{__init__.py, logger.py, time.py}
```

**Library: vertical slices.** Use this for a shared `<app>-core` package once one exists.

```
src/<app>_core/
  __init__.py
  core/                  domain verticals, one folder per domain
    <domain>/
      __init__.py        facade: re-exports + __all__
      models.py          every model of the vertical (models/ package once it outgrows a file)
      spec.py            catalog spec, if the vertical is a plugin catalog
      base.py            ABC for plugin implementations
      registry.py        Registry instance + @register_<kind> decorator
      <impl>/{__init__.py, <role>.py}   e.g. stripe/provider.py: the file is named for its role
  lib/                   primitives: config.py, db/, exceptions/, http/, redis/, utils/
  client/                async SDK client, private modules start with `_` (_http.py, _errors.py)
  cli/                   CLI entrypoint, if any
```

## Where a file goes

- Models go in `models.py` / `models/<entity>.py`. Catalog specs go in `spec.py`, ABCs in
  `base.py`, settings in `config.py`.
- **A module that does something defines no models.** That covers services, routes,
  `registry.py` and package `__init__.py` files. A dataclass that carries behaviour stays with
  the logic that uses it.
- Constants live at the top of the module that uses them. There is no `constants.py`.
- One outbound client per sibling service, in `<sibling>_client.py`. It is the only place that
  attaches internal credentials and maps transport failures to `UpstreamError`.

## Layering

| Layer | May import |
|---|---|
| `api/routes` | `api/deps`, `services`, `models`, `config`. Repositories only for a trivial read |
| `api/deps` | `config`, `api/access`, `repositories`, `services` |
| `services` | `repositories`, other `services`, `models`, `config`, `engine` |
| `repositories` | `models`, `lib/db` |
| `engine` / worker | `services`, `repositories`, `config` |
| `lib` | the standard library and third-party code only. Never the app, never FastAPI |

The arrows point one way. If a service needs something from `api`, that something belongs
in a service or in `lib`.

## `__init__.py`: three kinds

1. **Empty, zero bytes.** This is the default for app layer packages (`api/`, `services/`,
   `repositories/`, `models/`, `tests/`).
2. **Docstring only.** Use it when the package needs a sentence, e.g. `api/deps` saying there
   are no re-exports.
3. **Facade.** A package docstring, explicit re-exports and `__all__`. Use it only for library
   packages and `lib/*` packages. A facade may import plugin modules for their side effect
   (`# noqa: F401`) so built-ins register.

The top-level `src/<pkg>/__init__.py` holds a one-line docstring and nothing else.

## File naming

- snake_case everywhere.
- **Plural nouns** for route modules and packages: `routes/notes.py`,
  `routes/spend_limits.py`.
- **Singular nouns** for model modules: `models/note.py`.
- `<domain>_service.py`, `<entity>_repository.py`, `<thing>_middleware.py`.
- A module that is private to its package starts with `_` (`client/_http.py`). Its public
  names are re-exported by the package facade.
- Related small classes share a file. Two repositories of one domain, or a model with its
  `Page` and `Create` shapes, go together.

## Size

- **Modules:** median about 90 lines, p90 under 300. When a module passes about 400 lines,
  split it by concern into a package rather than adding section banners.
- **Functions:** median 8–14 lines, p90 under 40. A long route handler means the work belongs in
  a service.

## Adding a resource (vertical checklist)

For a new resource `invoice`:

1. `models/invoice.py`: `class Invoice(BaseModel, table=True)` with `__tablename__ = "invoices"`
   and a `patchable` set. Add `InvoicePage` and `InvoiceCreate` (only if needed) in the same
   file.
2. `repositories/invoice_repository.py`: `InvoiceRepository(BaseRepository[Invoice])` with the
   scoped lookups.
3. `services/invoice_service.py`: `InvoiceService` with static methods `list_page`, `get`,
   `create`, `update`, `delete`.
4. `api/routes/invoices.py`: `router = APIRouter()`, then the handlers `list_invoices`,
   `get_invoice`, `create_invoice`, `update_invoice`, `delete_invoice`.
5. Mount it in `api/routes/__init__.py`: `prefix="/invoices"`, `tags=["invoices"]`.
6. `migrations/versions/NNNN_invoices.py` creates the table. Import the model in
   `migrations/env.py` and `tests/conftest.py`.
7. `tests/test_invoices.py`: behaviour-named tests through the service and the HTTP surface.

## Growing

Start with one service repo. Split only when a second consumer exists.

**A second process (worker, scheduler).** Add `worker.py` with a `main()` that starts and stops
the same `config.py` singletons. Ship it from the same image and pick the process with the
command. Put its execution code under `engine/`.

**A second service.** Create `<app>-<role>` from the same template.

**A shared library.** Extract one when a second service needs the same models or primitives.

1. Create `<app>-core` with the library shape. Move `lib/` from the first service into
   `<app>_core/lib/` unchanged, then change every import from `<pkg>.lib.…` to
   `<app>_core.lib.…`. Do not leave re-export shims behind.
2. Move each table model that a second service reads into `<app>_core/core/<domain>/models.py`.
   Models only one service reads stay in that service's `models/`.
3. `CoreSettings` moves with `lib/config.py`. Each app keeps instantiating **both** its own
   `<Role>Settings` and `CoreSettings`, as parallel reads of the same environment. Never
   inherit from `CoreSettings`.
4. Services depend on the library by git URL in `pyproject.toml`. Refresh it with
   `uv lock --upgrade-package <app>-core && uv sync`.
5. The library never reads the environment, never opens a connection on import, and never
   imports FastAPI.

**An edge service in front of an execution service.** When one service should own identity
and tenancy and another should own the work:

- The edge verifies the caller and resolves scope (org, project, role).
- It forwards that scope as trusted headers, protected by a shared internal secret.
- The inner service admits only the edge, through middleware that fails closed, and trusts the
  forwarded scope.
- No bearer token crosses the seam.
- Each service owns its own database and its own Alembic tree.
