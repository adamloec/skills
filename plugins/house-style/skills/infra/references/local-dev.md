# Local dev rig

The rig lives in `{{app}}-charts/local/` and builds the sibling app repos from source.

```
local/
  docker-compose.yml
  .env.example            copied to local/.env (gitignored) by `make setup`
  postgres/init.sql       one database per service, created on first volume init
  fixtures/               optional one-shot seed service (see below)
```

## Compose conventions

- **One section per tier, with a banner comment:** `# ── Data ──`, `# ── Backend ──`,
  `# ── Frontend ──`, `# ── Fixtures (dev seed) ──`.
- **Service names:**
  - Infra uses its plain name: `postgres`, `redis`, `minio`.
  - Apps use their repo name: `{{app}}-api`, `{{app}}-web`, `{{app}}-worker`.
  - One-shot initializers are `<svc>-init`.
  - The seed is `{{app}}-fixtures`.
- **App services build from the sibling repo with the token secret:**
  ```yaml
  build:
    context: ../../{{app}}-api
    secrets: [gh_token]
  ```
  ```yaml
  secrets:
    gh_token:
      environment: GH_TOKEN
  ```
- **One image, several services.** An API and its worker build the same context and differ only
  in `command:`.
- **Env is inline per service.** There is no `env_file:`. Each value is
  `${VAR:-deterministic-dev-default}`, named so it is obviously not a production value:
  `${INTERNAL_SECRET:-dev-internal-secret-not-for-production}`.
  - Backend services get `{{APP}}_`-prefixed vars that mirror the chart's env.
  - Web apps get their unprefixed vars (`API_URL`, `AUTH_*`, `REDIS_URL`).
- **Security gates stay on in dev.** An empty secret disables a gate, so the rig sets a
  deterministic value to keep the protected path exercised.
- **Healthchecks on every service that something depends on:**
  - `postgres`: `pg_isready -U {{app}}`
  - `redis`: `redis-cli ping`
  - Python app: python, because the slim image has no curl:
    ```yaml
    healthcheck:
      test: ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\""]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    ```
- **`depends_on` always names a condition:** `service_healthy`, `service_started` or
  `service_completed_successfully` (for init containers).
- **Profiles:** the core stack has none. Extras go behind `dev` (debug UIs) and
  `integrations` (vendor stand-ins).
- **Volumes** are named `<svc>_data`. Config is bind-mounted `:ro`, straight from the chart
  where one exists, so the rig and a deployment can't drift.
- **Image pins match the chart's.** That equality is the drift check.

## Ports

| What | Host | Container |
|---|---|---|
| Infra | native (5432, 6379, 9000…) | native |
| Python API | **8001** | 8000 |
| Internal-only API | `127.0.0.1:<port>` (loopback only) | its port |
| Browser-facing web app or edge | **3000** | 3000 |
| Vendor mocks | 8090, 8091, … | — |
| Dev UIs | 8025, 8081, … | — |

When there are several browser-facing apps, put a Caddy `edge` in front. It becomes the only
service publishing a browser port, and it routes `*.localhost` hostnames (`app.localhost:3000`,
`auth.localhost:3000`). Containers that must resolve the same names get
`extra_hosts: ["auth.localhost:host-gateway"]`.

## `postgres/init.sql`

```sql
-- Runs only when the postgres volume is first created. One database per service.
CREATE DATABASE {{app}}_api;
```

## Fixtures (dev seed)

The seed is an optional one-shot service built from `local/fixtures/`, a small uv package that
imports the app's SDK or calls its API.

- It has `restart: "no"` and depends on the API being `service_healthy`.
- It is idempotent: it skips anything whose display name already exists. It supports
  `--dry-run`, and one fixture failing doesn't stop the rest.
- The catalog is bind-mounted `:ro`, one folder per item. Secrets come from `${ENV}`
  interpolation, never committed.

## Makefile (charts repo root)

```make
COMPOSE := docker compose -f local/docker-compose.yml

up:            ; $(COMPOSE) up -d --build
up-dev:        ; $(COMPOSE) --profile dev up -d --build
down:          ; $(COMPOSE) --profile '*' down
logs:          ; $(COMPOSE) logs -f
ps:            ; $(COMPOSE) ps
setup:         ; ./scripts/setup-local.sh
```

`scripts/setup-local.sh` copies `.env.example` to `.env` if it is absent, runs `up`, and prints
the URLs.

## Running one app on the host

Stop its container (`docker compose stop {{app}}-web`) and run it with live reload. It reaches
the rig on the published ports (`API_URL=http://localhost:8001`).
