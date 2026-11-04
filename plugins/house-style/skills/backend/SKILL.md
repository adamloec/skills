---
name: backend
description: House style and scaffold for backend Python — uv, FastAPI, SQLModel on async SQLAlchemy, Alembic, pydantic-settings, structlog, pytest. Use when starting a new backend service or shared library from an app idea, or when adding or editing any Python in a backend repo (routes, deps, services, repositories, models, migrations, settings, env vars, errors, logging, tests), so the repo layout, file anatomy, naming, config and code shape match the house blueprint exactly.
when_to_use: New API or service, "scaffold the backend", "add an endpoint/table/migration/setting", Python file structure, naming a class/function/module/env var, pyproject or tests setup.
---

# Backend house style

This is the blueprint for every backend I build. Follow it exactly. When an existing repo
already deviates, match the repo in that file and follow this guide for anything new.

**Stack:** Python 3.13 · uv · FastAPI · SQLModel (SQLAlchemy 2 async, asyncpg) · Alembic ·
pydantic-settings · structlog · pytest + pytest-asyncio (auto mode) · aiosqlite for tests ·
httpx2 for HTTP and test clients · ruff (lint only).

## Placeholders

Templates under `templates/` use these tokens. Pick the values once, from the app idea:

| Token | Meaning | Example |
|---|---|---|
| `{{app}}` | short app slug, lowercase | `acme` |
| `{{App}}` | display name, PascalCase | `Acme` |
| `{{APP}}` | env var prefix, no trailing underscore | `ACME` |
| `{{dist}}` | repo / distribution name, kebab | `acme-api` |
| `{{pkg}}` | import package, `{{dist}}` with underscores | `acme_api` |

Repos are named `<app>-<role>`: `acme-api`, `acme-worker`, `acme-core` (shared library),
`acme-web`. Every service of one app shares the one `{{APP}}_` env prefix.

## Workflow

### A. New service from an app idea

1. Copy `templates/service/` to the new repo root, including dotfiles.
2. Rename the `src/{{pkg}}` directory, then substitute every token in every file:
   ```bash
   mv 'src/{{pkg}}' src/acme_api
   grep -rl '{{' . | xargs sed -i -e 's/{{pkg}}/acme_api/g' -e 's/{{dist}}/acme-api/g' \
     -e 's/{{APP}}/ACME/g' -e 's/{{App}}/Acme/g' -e 's/{{app}}/acme/g'
   ```
3. The template ships one example resource, `notes`, wired through every layer (model →
   repository → service → route → migration → tests). Rename it to the app's first real
   resource, or use it as the pattern and delete it. Do not leave it in.
4. `api/deps/identity.py` ships `require_user` failing closed (401). Wire in the real verifier,
   such as OIDC JWT verification against the issuer's JWKS, before any route goes live.
   Rename `ServiceSettings` to `<Role>Settings`.
5. Add the app's real resources one vertical at a time, each through all layers (see
   `references/layout.md`, "Adding a resource").
6. `uv lock && uv sync && uv run ruff check && uv run pytest` must pass.
7. Then use the **infra** skill for the Dockerfile, entrypoint, CI and local compose, and the
   **frontend** skill for the web app.

Start with **one service repo**. Its `lib/` package holds the infrastructure primitives (db,
exceptions, logging, time). When a second service needs the same models or primitives, extract
a shared library: see `references/layout.md`, "Growing".

### B. Working in an existing repo

Read the reference for the piece you are touching before writing it:

| Touching | Read |
|---|---|
| where a file goes, module names, `__init__.py`, when to split | `references/layout.md` |
| any new `.py` file: docstrings, imports, ordering, formatting | `references/python-file.md` |
| naming a class, function, variable, column, test | `references/naming.md` |
| function signatures, class kinds, services, repositories, enums | `references/code-shape.md` |
| settings, env vars, `config.py`, secrets, defaults | `references/config.md` |
| app, lifespan, routers, routes, deps, middleware, pagination | `references/api.md` |
| tables, ids, timestamps, transactions, Alembic | `references/data.md` |
| exceptions, HTTP mapping, structured logs | `references/errors-and-logging.md` |
| tests, fixtures, factories | `references/testing.md` |

## The non-negotiables

1. **src layout, absolute imports only.** `src/<pkg>/…`, never a relative import.
2. **One direction:** `api/routes` → `services` → `repositories` → `models`. Services never
   import `api`. Repositories never import services. A shared library never imports an app or
   FastAPI.
3. **Docstrings on declarations, zero comments in function bodies.** Every module starts with a
   docstring. Google style. Explain the contract, not the implementation. If a line needs a
   comment, give it a name instead. Tooling pragmas (`# noqa`, `# type: ignore[...]`) are fine.
4. **Type everything, modern syntax.** `X | None`, `list[str]`, `collections.abc` types, no
   `Optional`/`List`/`Dict`. Return types on every function.
5. **Async for anything that touches I/O.** Pure helpers stay sync.
6. **Services are stateless classes of `@staticmethod`s**, one per domain, in
   `services/<domain>_service.py`. `session` is always the first argument, and scope and options
   are keyword-only after `*`.
7. **Repositories are per-session instances** subclassing `BaseRepository[Model]`, in
   `repositories/<entity>_repository.py`. Scoped reads take the owner id first.
8. **One model per entity.** The table model is the response model. Partial updates go through
   the model's `patchable` set and `validate_patch`. There are no `*Update`, `*Read` or
   `*Response` DTOs. `<Entity>Create` exists only when the create body truly differs.
9. **Typed errors below the route.** Services and repositories raise the app's exception
   hierarchy (`NotFoundError`, `ConflictError`…), never `HTTPException`. One handler turns them
   into a uniform JSON envelope.
10. **Settings are classes, `config.py` is the composition root.** `{{APP}}_`-prefixed env vars,
    local-dev defaults, `extra="ignore"`. `config.py` instantiates settings and builds the infra
    singletons with no I/O. The `lifespan` in `main.py` starts and stops them. Libraries never
    read the environment.
11. **Alembic owns the schema.** Never `create_all` at runtime. Migration files are
    `NNNN_snake_slug.py` and the revision id is the file stem.
12. **Aware UTC everywhere:** the `UTCDateTime` type and `utcnow()`, never `datetime.now()`.
13. **Structured logs:** `logger.info("Constant sentence", key=value)`, never f-strings.
14. **Fail closed.** An empty secret disables the feature or rejects the caller. It never opens
    a door.
15. **Keyset pagination** on growing tables: `(created_at, id)` order, `limit + 1`, an opaque
    `next_cursor`.
16. **Tests run offline** against in-memory SQLite through the real repositories and services.
    Anything that needs live infrastructure is marked and skipped by default.
17. **No private or one-off functions.** Every function is public, documented, and lives with the
    concept it serves: a service static method, a model method or classmethod, a repository
    query, or the public contract of a `lib/` module. Logic with one caller stays inline, with
    well-named locals. A leading underscore is used only for instance state (`self._client`):
    never for functions, modules or constants.

## Service shape at a glance

```
{{dist}}/
├── pyproject.toml  uv.lock  .python-version  alembic.ini  README.md
├── migrations/  env.py  script.py.mako  versions/0001_baseline.py
├── src/{{pkg}}/
│   ├── __init__.py          one-line package docstring
│   ├── main.py              FastAPI app, lifespan, /health, /readiness
│   ├── config.py            <Role>Settings + infra singletons (composition root)
│   ├── api/
│   │   ├── context.py       frozen per-request context (Principal)
│   │   ├── deps/            session.py, identity.py … (one dependency family per file)
│   │   ├── middleware/      exception_handler.py, <thing>_middleware.py
│   │   └── routes/          __init__.py builds the /v1 router; <resources>.py per resource
│   ├── services/            <domain>_service.py
│   ├── repositories/        <entity>_repository.py
│   ├── models/              <entity>.py (table models + their page/create shapes)
│   └── lib/                 config.py (CoreSettings), db/, exceptions/, utils/ — what a
│                            future shared library takes over unchanged
└── tests/  conftest.py  test_<behaviour>.py
```

## Before you finish

- [ ] Every new module, class and function has a docstring. No body comments.
- [ ] No `_private` functions, no `_private.py` modules, and no one-off helpers. Logic lives on
      the class that owns it, or stays inline.
- [ ] Imports are absolute, grouped stdlib / third-party / first-party, and sorted.
- [ ] Names follow `references/naming.md`: service, repository and route verbs, `XDep`
      aliases, `is_` flags, unit-suffixed numbers.
- [ ] Each new setting is a field on a settings class, has a dev default, and is listed in the
      README's configuration table. A secret's default is `""`.
- [ ] Each schema change has a migration with the next `NNNN_` number and a docstring that says
      whether it is rolling-safe.
- [ ] `uv run ruff check` and `uv run pytest` pass.
