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
