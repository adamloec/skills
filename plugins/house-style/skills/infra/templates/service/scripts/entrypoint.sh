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
