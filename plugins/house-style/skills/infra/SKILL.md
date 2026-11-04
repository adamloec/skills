---
name: infra
description: House style and scaffold for deployment and ops — Dockerfiles for uv/FastAPI services and pnpm/Next.js standalone apps, the migrate-then-exec entrypoint, a docker-compose local dev rig, a Helm chart with folder-per-component templates and secretKeyRef env wiring, GitHub Actions CI with immutable sha tags and a values bump, and chart releases from a CHANGELOG. Use when containerizing or deploying an app, adding a component, env var, secret, port, job, ingress host or workflow, or setting up local dev, so images, charts, env wiring and pipelines match the house blueprint exactly.
when_to_use: Dockerfile, docker compose, local dev rig, Helm chart/values/templates, Kubernetes env vars and secrets, CI/CD workflows, image tags, releasing, renovate.
---

# Infra house style

This is the blueprint for how every app I build is packaged, run locally, deployed and
released. Follow it exactly. It pairs with the **backend** and **frontend** skills: their
templates produce the code, and these templates ship it.

## Placeholders

| Token | Meaning | Example |
|---|---|---|
| `{{app}}` | short app slug, lowercase | `acme` |
| `{{App}}` | display name | `Acme` |
| `{{APP}}` | backend env prefix | `ACME` |
| `{{pkg}}` | backend import package | `acme_api` |
| `{{org}}` | GitHub owner of the repos and the registry | `acme-co` |

## Repos

Start small. Three repos is the minimum, and each repo is one release cadence and one trust
boundary:

| Repo | Holds | Template |
|---|---|---|
| `{{app}}-api` | the backend, its `Dockerfile`, `.dockerignore`, `scripts/entrypoint.sh`, `.github/workflows/ci.yml` | `templates/service/` |
| `{{app}}-web` | the web app, its `Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml` | `templates/web/` |
| `{{app}}-charts` | the Helm chart, the local dev rig, the reusable build-and-deploy workflow, chart publishing | `templates/charts-repo/` |

Clone them side by side (`~/src/{{app}}-api`, `~/src/{{app}}-web`, `~/src/{{app}}-charts`).
The compose rig builds the sibling repos by relative path.

Add these later, only when needed:
- `{{app}}-core`, a shared Python library (backend skill, `layout.md` → "Growing")
- `{{app}}-packages`, shared TS packages (frontend skill, `packages.md`)
- `<client>-env`, per-environment pins for GitOps (`references/releasing.md`)

## Workflow

### A. Ship a new app

1. Copy `templates/service/*` into the API repo, `templates/web/*` into the web repo, and
   `templates/charts-repo/*` into a new `{{app}}-charts` repo. Include dotfiles. Substitute the
   tokens:
   ```bash
   grep -rl '{{' . | xargs sed -i -e 's/{{pkg}}/acme_api/g' -e 's/{{APP}}/ACME/g' \
     -e 's/{{App}}/Acme/g' -e 's/{{app}}/acme/g' -e 's/{{org}}/acme-co/g'
   mv 'charts/{{app}}' charts/acme   # in the charts repo
   ```
   Helm's own `{{ … }}` template syntax is untouched, because none of it matches a token.
2. `cd {{app}}-charts && make up`. Postgres, the API and the web app run locally from source.
3. `make helm-deps && make helm-lint`. This vendors the Postgres subchart and renders the chart.
   Commit `charts/*.tgz` and `Chart.lock`.
4. Set the org secrets the workflows expect: `BUILD_TOKEN` (reads private deps) and
   `INFRA_TOKEN` (pushes the values bump to the charts repo).
5. Each new backend setting or web env var gets wired in **three places** in the same change:
   - the compose service's `environment:` (with a dev default)
   - the chart's deployment `env:` (plain `value`, or `secretKeyRef`)
   - the app README's configuration table

   See `references/env-and-secrets.md`.

### B. Changing infra in an existing app

| Touching | Read |
|---|---|
| a Dockerfile, `.dockerignore`, the entrypoint | `references/docker.md` |
| compose services, ports, dev defaults, seed data | `references/local-dev.md` |
| chart layout, values, templates, helpers, jobs, ingress, probes | `references/helm.md` |
| an env var or secret, end to end | `references/env-and-secrets.md` |
| CI, image tags, values bumps, chart releases, renovate | `references/releasing.md` |
| any name: image, resource, values key, secret, port, database | `references/naming.md` |

## The non-negotiables

1. **Images are environment-agnostic.** Never use build args. All config arrives at runtime as
   env vars or mounted secrets. One image runs in every environment, and the Dockerfile says so
   in a comment.
2. **Build secrets go only through BuildKit** (`--mount=type=secret,id=gh_token`). The token is
   written, used and deleted in one `RUN`. A committed `.npmrc` holds only the scope → registry
   mapping.
3. **Migrations run in the entrypoint.** It runs `alembic upgrade head` in a retry loop, which
   doubles as wait-for-DB, under a per-service advisory lock, then `exec "$@"`. Consequences:
   - Deployments that migrate use `strategy: Recreate`.
   - Charts pass commands as `args:`, never `command:`.
4. **Immutable tags.** CI pushes `sha-<7>` (plus `latest`, which is never consumed) and bumps
   the chart's values. Charts reference only `sha-*`.
5. **Publishing is not deploying.** A chart release is a `version:` bump plus a CHANGELOG
   section in the same commit. A deploy is moving a pin. Published versions are immutable, and
   a rollback is a re-pin.
6. **Secrets never live in values or git for production.** Use `secretKeyRef` to a named
   Secret. `create: false` by default. Registry and cloud credentials come from installer
   scripts, never from the chart.
7. **Fail closed, fail loud.** Use `required` and `fail` with a full-sentence message at render
   time. Empty means disabled. Security gates stay on in dev, with deterministic dev secrets.
8. **One definition per concern.** Shared env blocks are `_helpers.tpl` helpers, so two
   deployments can't drift.
9. **Comments carry the why** in Dockerfiles, values, templates and workflows. They name the
   failure a line prevents. YAML and Dockerfiles are where this kind of rationale *is* allowed.
10. **Minimal surface:** `revisionHistoryLimit: 3`, resource requests without limits, no probes
    unless a bad rollout would be catastrophic (and then a comment says so), and NetworkPolicies
    on for internal-only services.

## Before you finish

- [ ] No `ARG` in any Dockerfile. Build secrets use `--mount=type=secret`.
- [ ] Every new env var is in the compose environment, the chart env and the README table.
- [ ] Every secret is a `secretKeyRef`. Nothing secret sits in `values.yaml` defaults.
- [ ] Any chart change bumps `version:` and adds a `## [x.y.z]` CHANGELOG section.
- [ ] `make helm-lint` passes. `docker compose config` parses.
