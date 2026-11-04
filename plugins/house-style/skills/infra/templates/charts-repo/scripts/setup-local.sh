#!/usr/bin/env bash
# Bring up the local dev rig.
#
# Copies local/.env.example to local/.env if it is absent, builds and starts the stack, and
# prints where everything is. Idempotent: re-running keeps an existing .env and rebuilds.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

log() { printf '\033[1m[setup]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[setup]\033[0m %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null || die "docker is not installed"
docker compose version >/dev/null 2>&1 || die "docker compose v2 is required"

if [ ! -f "$ROOT/local/.env" ]; then
  cp "$ROOT/local/.env.example" "$ROOT/local/.env"
  log "created local/.env from .env.example"
fi

docker compose -f "$ROOT/local/docker-compose.yml" up -d --build

log "web:      http://localhost:3000"
log "api:      http://localhost:8001 (docs at /docs)"
log "postgres: localhost:5432 (user {{app}})"
log "next: make logs"
