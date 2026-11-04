# Docker

## Python service (uv + FastAPI)

```dockerfile
FROM python:3.13-slim
# git: private dependencies resolve by git URL.
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
WORKDIR /app

# Dependencies first, in their own cached layer. gh_token authorizes private git deps and is
# removed in the same layer, so it never lands in the image.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=secret,id=gh_token,required=false \
    if [ -f /run/secrets/gh_token ]; then \
      git config --global url."https://x-access-token:$(cat /run/secrets/gh_token)@github.com/".insteadOf "https://github.com/"; \
    fi && \
    uv sync --frozen --no-dev --no-install-project && \
    rm -f ~/.gitconfig

COPY src/ src/
COPY alembic.ini ./
COPY migrations/ migrations/
COPY scripts/ scripts/
RUN chmod +x scripts/entrypoint.sh && uv sync --frozen --no-dev

# No build args, and none are coming: all config is runtime env, so the image is identical in
# every environment.
EXPOSE 8000
# Migrates (advisory-locked), then execs CMD. Deployments pass their command as `args:`.
ENTRYPOINT ["./scripts/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "{{pkg}}.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- **Base image** is `python:3.13-slim`, matching `.python-version`. uv is copied from its image,
  pinned to a minor version.
- **apt** installs only what is needed: `--no-install-recommends`, then clear the lists. Any
  native library gets a comment saying why.
- **Two-phase `uv sync`:** dependencies (`--no-install-project`) first, then the project.
  `README.md` is copied early because `pyproject.toml` names it.
- **One image, several processes.** An API and a worker share the image and differ only in the
  command:
  - `CMD` is the most common process.
  - Every other process passes its command through `args:` in the chart, or `command:` in
    compose (compose `command:` replaces CMD and still runs through the ENTRYPOINT).
- **Multi-stage only when it adds something,** e.g. a stage that builds a wheel to serve.
- There is no `HEALTHCHECK` in the image. Health is declared in compose and the chart.
- The app exposes `/health` (204, no I/O), and `/readiness` (204, or 503 when the database is
  down).

### `scripts/entrypoint.sh`

```sh
#!/bin/sh
# Container entrypoint: bring the schema to head, then exec the process.
#
# Every container runs this. Concurrent boots are safe because migrations/env.py holds a
# Postgres advisory lock for the upgrade: the winner migrates, the rest block, then see head.
# The retry loop doubles as wait-for-DB on a cold start.
set -eu

echo "[entrypoint] alembic upgrade head…"
n=0
until uv run alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 30 ]; then
    echo "[entrypoint] migrations still failing after $n attempts; giving up" >&2
    exit 1
  fi
  echo "[entrypoint] attempt $n failed (DB not ready?); retrying in 5s…" >&2
  sleep 5
done

echo "[entrypoint] schema at head; starting: $*"
exec "$@"
```

The advisory-lock key is distinct per service (`LOCK_KEY` in `migrations/env.py`), because
advisory locks are instance-wide on a shared Postgres.

## Next.js standalone app (pnpm)

```dockerfile
FROM node:24-alpine AS base
RUN corepack enable && corepack prepare pnpm@11.15.1 --activate

FROM base AS deps
WORKDIR /app
# pnpm-workspace.yaml carries the allowBuilds approvals; without it native binaries don't install.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# A private registry token goes in a user-level npmrc, removed in the same layer. pnpm ignores
# env-var expansion in a project .npmrc's credentials.
RUN --mount=type=secret,id=gh_token,required=false \
    if [ -f /run/secrets/gh_token ]; then \
      printf '//npm.pkg.github.com/:_authToken=%s\n' "$(cat /run/secrets/gh_token)" > /root/.npmrc; \
    fi && \
    pnpm install --frozen-lockfile && \
    rm -f /root/.npmrc

FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# No build args, and none are coming: every value is read server-side at request time, so the
# image is identical in every environment.
ENV CI=true
RUN pnpm --config.verify-deps-before-run=false build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
```

- Use four stages: `base` → `deps` → `build` → `runner`. The pnpm version equals
  `packageManager`.
- Add `COPY --from=build /app/public ./public` when the app has a `public/` directory.
- Add `.npmrc` to the deps `COPY` once there is a private scope.
- `next.config.ts` must set `output: "standalone"`.
- The only ENV baked in is `NODE_ENV`, `PORT`, `HOSTNAME`, and `CI` in the build stage.
- The runner is non-root (uid 1001).

## `.dockerignore`

Exclude host dependencies and build output, VCS, editor files, local env files, and anything
that must never be served. Give each non-obvious line a comment.

```
# Never ship the host's install or build output: a host node_modules or .venv built for another
# platform breaks in the container.
node_modules
.next
.venv
__pycache__
.pytest_cache
.ruff_cache
.git
.gitignore
.dockerignore
Dockerfile
.env*
.vscode
.idea
.DS_Store
*.tsbuildinfo
```
