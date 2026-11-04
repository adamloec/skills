# {{App}} Charts

The deployment side of {{App}}: the Helm chart, the local dev rig, and the reusable workflow
every app repo's CI calls to build its image and bump its tag here.

Publishing is not deploying. A push to an app's `main` writes a `sha-` tag into
`charts/{{app}}/values.yaml` (a candidate). Bumping `Chart.yaml` `version:` with a CHANGELOG
section publishes an immutable chart. Moving an environment's pin to it is the deploy.

## Layout

```
charts/{{app}}/       the chart: Chart.yaml, CHANGELOG.md, values.yaml, templates/<component>/
local/                docker-compose dev rig + .env.example + postgres/init.sql
scripts/              setup-local.sh
.github/workflows/    ci.yml, build-and-deploy.yml (reusable, @v1), chart-publish.yml
```

## Local dev

Clone `{{app}}-api`, `{{app}}-web` and this repo side by side, then:

```bash
make setup     # creates local/.env, builds and starts everything
make logs
make down
```

| Service | URL |
|---|---|
| web | http://localhost:3000 |
| api | http://localhost:8001 |
| postgres | localhost:5432 |

## Chart

```bash
make helm-deps      # vendor subcharts; commit charts/*.tgz and Chart.lock
make helm-lint
make helm-template
```

Every first-party component has the same values shape: `replicaCount`,
`image.{repository,tag}`, `port`, `command`, `env`, `resources`.

## Releasing

1. Bump `charts/{{app}}/Chart.yaml` `version:` (patch for image-only, minor for templates or
   values, major for a breaking values schema).
2. Add the `## [x.y.z]` section to `CHANGELOG.md` in the same commit.
3. Push to `main`. `chart-publish.yml` packages, pushes `oci://ghcr.io/{{org}}/charts/{{app}}`,
   tags `{{app}}-x.y.z`, and creates the GitHub release.
