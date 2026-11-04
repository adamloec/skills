# Infra naming

| Thing | Convention | Example |
|---|---|---|
| Repos | `<app>-<role>` | `{{app}}-api`, `{{app}}-web`, `{{app}}-charts`, `{{app}}-core`, `<client>-env` |
| Image | `ghcr.io/<org>/<repo>` | `ghcr.io/{{org}}/{{app}}-api` |
| Image tag | `sha-<first 7 of commit>` | `sha-ce3ac3c` |
| Chart | `oci://ghcr.io/<org>/charts/<chart>` | `.../charts/{{app}}` |
| K8s resource | `<app>-<component>`, kebab; Deployment = Service = container = `app` label | `{{app}}-api`, `{{app}}-worker` |
| Job / CronJob | `<app>-<verb>-<noun>` | `{{app}}-preflight`, `{{app}}-reconcile-invoices` |
| Template dir | component, kebab, no app prefix | `api/`, `runtime-api/` |
| Values key | camelCase, no app prefix | `api`, `runtimeApi`, `web` |
| Per-component keys | `replicaCount`, `image.{repository,tag}`, `port`, `command`, `env`, `resources`, `networkPolicy.enabled` | — |
| Feature toggle | `<feature>.enabled`; host/endpoint `""` = off | `secretInit.enabled`, `docs.host: ""` |
| Secret | `<app>-<purpose>`; keys kebab-case | `{{app}}-secrets` → `internal-secret`, `auth-secret` |
| TLS secret | `<app>-tls`, `<app>-<host>-tls` | `{{app}}-tls` |
| Helpers | `<app>.fullname`, `<app>.labels`, `<app>.<concern>Env`, `<app>.<derivation>` | `{{app}}.dbEnv`, `{{app}}.publicOrigin` |
| Databases | one per service, snake_case, in a shared Postgres | `{{app}}_api`, `{{app}}_worker` |
| Redis | one instance; one DB index per consumer, documented in a comment; plus a key prefix per app | sessions on DB 2 with `SESSION_KEY_PREFIX` |
| Container ports | Python API 8000, a second Python API 8002, Next apps 3000 | — |
| Local host ports | API 8001 → 8000; internal APIs on loopback; browser edge 3000 | — |
| Compose services | infra plain name; apps by repo name; initializers `<svc>-init` | `postgres`, `{{app}}-api`, `minio-init` |
| Volumes | `<svc>_data` | `postgres_data` |
| Workflows | `ci.yml` (`name: CI`), `build-and-deploy.yml`, `chart-publish.yml` | — |
| Scripts | `scripts/entrypoint.sh` (app), `scripts/setup-local.sh`, `scripts/<target>-install.sh` | `bootstrap-install.sh` |
| Make targets | `up`, `up-dev`, `down`, `logs`, `ps`, `setup`, `helm-deps`, `helm-lint`, `helm-template` | — |

## Shell scripts

- Bash scripts start with `#!/usr/bin/env bash` and `set -euo pipefail`. Container entrypoints
  use POSIX `sh` with `set -eu`.
- A header comment covers usage, what the script does and why, and "Idempotent: re-running …".
- Pinned constants go at the top, with a comment naming them as the single source.
- Use `die()` / `log()` helpers, a `usage()` heredoc, and a `while case` argument parser.
- Preflight the tools and the cluster (`command -v kubectl`, `kubectl cluster-info`).
- Make applies idempotent: `kubectl create … --dry-run=client -o yaml | kubectl apply -f -`,
  and `helm upgrade --install … --wait`.
- End by printing the next steps.
