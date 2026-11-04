# {{App}} API

One paragraph: what this service owns, and what it deliberately does not (the seam against its
neighbors).

## Layout

```
src/{{pkg}}/
  main.py        FastAPI app, lifespan, /health, /readiness
  config.py      settings + infra singletons
  api/           deps/, middleware/, routes/ (one module per resource)
  services/      one stateless service class per domain
  repositories/  one repository per entity
  models/        table models and their page shapes
  lib/           db, exceptions, logging, time primitives
migrations/      Alembic; NNNN_slug.py, revision id = file stem
tests/           offline pytest suite on in-memory SQLite
```

## Running locally

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn {{pkg}}.main:app --reload --port 8000
```

## Configuration

Every variable is `{{APP}}_` plus a settings field name. Defaults are the local dev rig's.

| Variable | Default | Purpose |
|---|---|---|
| `{{APP}}_DEBUG` | `true` | Console logs instead of JSON. |
| `{{APP}}_DATABASE_URL` | local Postgres | The service's own database. |
| `{{APP}}_DATABASE_POOL_SIZE` | `20` | Connections held per process. |
| `{{APP}}_PUBLIC_URL` | `http://localhost:3000` | The web app's public origin, for links. |

## Testing

```bash
uv run ruff check
uv run pytest            # offline
uv run pytest -m infra   # needs docker compose up -d
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "invoice due date" --rev-id 0002_invoice_due_date
uv run alembic upgrade head
```

Each revision's docstring states why it exists and whether it is rolling-safe.
