# Configuration and environment variables

## The model

- **Settings are `pydantic-settings` classes.** Their fields are the complete,
  self-documenting list of what the process reads from its environment.
- **`config.py` is the composition root.** It is the only module that instantiates settings,
  configures logging and constructs infrastructure singletons. Every other module imports what
  it needs from there: `from ledger_api.config import db, settings`.
- **Construction does no I/O.** `config.py` builds `Database`, `HttpPool`, `RedisClient` and
  similar objects cheaply at import. `main.py`'s lifespan (and `worker.py`'s `main()`) start
  them and stop them in reverse order.
- **A library never reads the environment.** It defines settings *classes* and infra
  *classes*. Apps instantiate them.

## Two settings classes from day one

| Class | Lives in | Holds |
|---|---|---|
| `CoreSettings` | `lib/config.py` | infrastructure every process of the app shares: `debug`, `database_*`, `redis_*`, `http_*`, queue/worker connection, `secrets_backend`, vault |
| `<Role>Settings` (`ServiceSettings` in the template; rename to `ApiSettings`, `WorkerSettings`…) | `config.py` | what only this service reads: secrets it checks, feature toggles, URLs of siblings, TTLs |

Both read the same `<APP>_` environment, as **parallel instances, never a subclass**. When a
shared library is extracted, `lib/config.py` moves with `lib/` unchanged.

## A settings class

```python
class ServiceSettings(BaseSettings):
    """Service settings, read from ``LEDGER_``-prefixed environment variables.

    ``internal_secret`` proves a call came from a sibling service; empty disables the gate on
    the receiving side, which then refuses every caller.
    ``invite_ttl_days`` bounds how long an invitation stays claimable; zero disables expiry.
    """

    model_config = SettingsConfigDict(env_prefix="LEDGER_", extra="ignore")

    internal_secret: str = ""

    invite_email_enabled: bool = False
    invite_ttl_days: int = 14

    s3_endpoint: str = ""
    s3_bucket: str = "ledger-files"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    public_url: str = Field(
        default="http://localhost:3000", description="The web app's public origin, for links.",
    )
```

**Rules:**

- `model_config = SettingsConfigDict(env_prefix="<APP>_", extra="ignore")`, on every settings
  class.
- **One prefix for the whole app.** Every service of the app reads `<APP>_…`, so a shared
  variable such as `<APP>_DATABASE_URL` or `<APP>_INTERNAL_SECRET` has a single spelling
  everywhere.
- **Flat fields, grouped by subsystem prefix**, with a blank line between groups:
  `database_*`, `redis_*`, `http_*`, `s3_*`, `<vendor>_*`. Do not nest models in settings.
- **Defaults are the local dev rig's values.** `uv run uvicorn …` works on a laptop with
  `docker compose up`. Deployments set every value explicitly.
- **A secret defaults to `""`, and empty means disabled.** The code that uses it fails closed:
  it refuses the caller, answers 503 or disables the feature. It never skips the check.
- **Document the non-obvious.** Put a short `Field(description=...)` on a field, or a paragraph
  per field in the class docstring when the explanation is long. An obvious field
  (`redis_url`) needs nothing.
- **Closed modes are `Literal`:** `auth_mode: Literal["oidc", "trusted-header"] = "oidc"`.
- **Lists are plural fields.** The env value is JSON: `LEDGER_ALLOWED_ORIGINS='["https://a"]'`.
  An empty list must have a defined meaning, which is usually "fail closed".
- **Derived defaults** use `@model_validator(mode="after")`, e.g. seeding an allowlist from
  the primary value. A suspicious value logs a warning in a `@field_validator` rather than
  being silently rewritten.
- **Derived URLs are functions** in `config.py` (`def token_url() -> str`), not fields.

## Field naming

The env var is the prefix plus the field name, upper-cased: `invite_ttl_days` →
`LEDGER_INVITE_TTL_DAYS`. So the field name *is* the env var name. Name it for an operator.

| Kind | Pattern | Example |
|---|---|---|
| Connection string | `<thing>_url` | `database_url`, `redis_url`, `public_url` |
| Host / port pair | `<thing>_host`, `<thing>_port` | `worker_host`, `worker_port` |
| Secret | `<purpose>_secret`, `<vendor>_token`, `<thing>_api_key`, `<thing>_secret_key` | `internal_secret`, `search_api_key` |
| Feature toggle | `<feature>_enabled` | `invite_email_enabled` |
| Global switch | bare adjective | `debug` |
| Duration | `<thing>_<unit>`, with unit `seconds`/`minutes`/`hours`/`days`/`ms` | `approval_timeout_hours`, `http_timeout_seconds` |
| Size / count | `<thing>_size`, `max_<things>`, `<thing>_limit` | `database_pool_size`, `http_max_connections` |
| File or dir | `<thing>_file`, `<thing>_dir`, `<thing>_path` | `catalog_file`, `exports_dir` |
| Bucket / queue / namespace | `<thing>_bucket`, `<thing>_queue`, `<thing>_namespace` | `s3_bucket`, `worker_task_queue` |
| Backend selector | `<thing>_backend` | `secrets_backend = "env"` |
| Version stamp | `version` | set by the deploy, empty in dev |

## `config.py` (service)

```python
"""Service settings and the live infra instances the rest of the app imports.

``CoreSettings`` and ``ServiceSettings`` are two parallel reads of the same environment, each
owning only its own fields. ``db`` is constructed here; its lifecycle belongs to ``main.py``.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from ledger_api.lib.config import CoreSettings
from ledger_api.lib.db import Database
from ledger_api.lib.utils.logger import setup_logging


class ServiceSettings(BaseSettings):
    ...


core = CoreSettings()
settings = ServiceSettings()

setup_logging(debug=core.debug)

db = Database(
    core.database_url,
    echo=core.database_echo,
    pool_size=core.database_pool_size,
    max_overflow=core.database_max_overflow,
    pool_timeout_seconds=core.database_pool_timeout_seconds,
    pool_recycle_seconds=core.database_pool_recycle_seconds,
)
```

The order is fixed: settings, then `setup_logging`, then the infra singletons, each built
from explicit keyword arguments. Never pass a settings object into an infra class.

## Secrets

- Secrets come from the environment. In a cluster they are mounted from a Secret through
  `secretKeyRef` (see the infra skill). Never commit them, and never put them in `values.yaml`
  defaults.
- When the app resolves credentials at runtime (per-tenant API keys and the like), it does so
  through a `secrets_backend` selector (`env` in dev, `vault` in a cluster) constructed in
  `config.py`.
- Never log a secret. Never put one in an exception's `context`.

## Who reads settings where

| Place | Reads |
|---|---|
| App modules | `from <pkg>.config import settings, db, …` |
| `migrations/env.py` | instantiates `CoreSettings` from `lib/config.py` directly. It does **not** import `config.py`, so a migration never constructs Redis or HTTP pools |
| Tests | never mutate settings. Override dependencies or construct the object under test with explicit arguments |
| Library code | takes values as constructor arguments only |

## README configuration table

Every service README has a configuration table, kept in sync with the settings class:

```markdown
| Variable | Default | Purpose |
|---|---|---|
| `LEDGER_DATABASE_URL` | local Postgres | The service's own database. |
| `LEDGER_INTERNAL_SECRET` | empty (gate refuses all) | Shared with sibling services. |
```

There is no `.env` file in the repo. Local values come from the defaults and the compose rig.
