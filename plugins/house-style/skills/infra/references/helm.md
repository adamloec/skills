# Helm chart

## Layout (`{{app}}-charts/charts/{{app}}/`)

```
Chart.yaml
Chart.lock               committed
CHANGELOG.md             Keep a Changelog; one section per version
values.yaml
values.schema.json       only for list-shaped declarations that need a schema
charts/*.tgz             vendored subcharts, committed (make helm-deps)
templates/
  _helpers.tpl
  api/        deployment.yaml  service.yaml  [networkpolicy.yaml] [<job>-job.yaml] [<task>-cronjob.yaml]
  web/        deployment.yaml  service.yaml
  worker/     deployment.yaml
  ingress.yaml           the whole public surface, one Ingress per host
  secrets.yaml           dev-only Secrets from values, behind <x>.create
```

**The naming chain:**

| Thing | Form | Example |
|---|---|---|
| Template dir | kebab, no app prefix | `runtime-api/` |
| Values key | camelCase, no app prefix | `runtimeApi` |
| Resource name | `<app>-<dir>` | `{{app}}-runtime-api` |

Resource names keep the prefix because they are Service DNS names that other things depend on.

## `Chart.yaml`

```yaml
apiVersion: v2
name: {{app}}
description: {{App}} application stack
type: application
# version is the release: one version = one tested, immutable bundle of templates + pinned image tags.
version: 0.1.0
appVersion: "0.1.0"
home: https://github.com/{{org}}/{{app}}-charts
sources:
  - https://github.com/{{org}}/{{app}}-charts
# Exact pins, matching the committed charts/*.tgz. A release is a pure function of the commit.
dependencies:
  - name: postgresql
    version: "16.7.27"
    repository: oci://registry-1.docker.io/bitnamicharts
    condition: postgresql.enabled
```

- **Exact dependency pins.** Vendor the `.tgz` and commit it together with `Chart.lock`. To
  upgrade: bump the pin, run `make helm-deps`, and commit all three together.
- Alias a hyphenated dependency to camelCase (`alias: certManager`) so `--set` stays readable.

## `values.yaml`

- **A banner comment per block,** with prose saying why.
- Global scalars at the top (`appUrl`, `ingress`).
- Then one camelCase key per first-party component.
- Then cross-cutting blocks.
- Then subchart pass-throughs.

```yaml
# ── API ───────────────────────────────────────────────────────────────────────
api:
  replicaCount: 1
  image:
    # Must match what the API repo's CI publishes. CI rewrites `tag` on every main push.
    repository: ghcr.io/{{org}}/{{app}}-api
    tag: sha-0000000
  port: 8000
  command: ["uv", "run", "uvicorn", "{{pkg}}.main:app", "--host", "0.0.0.0", "--port", "8000"]
  env:
    {{APP}}_DEBUG: "false"
  resources:
    requests: { cpu: 100m, memory: 256Mi }
```

**Rules:**

- Every component gets the same keys: `replicaCount`, `image.{repository,tag}`, `port`,
  `command`, `env`, `resources`, and `networkPolicy.enabled` when it has one.
- **Two image styles:**
  - First-party images split into `image.repository` + `image.tag`, where `tag` is `sha-<7>`
    and CI writes it.
  - Third-party images are one fully-qualified string, `image: docker.io/x/y:1.2.3`, so
    Renovate's regex manager can match it.
- **Feature toggles** are `<feature>.enabled`, off by default unless they are a security
  control. A host or endpoint is "empty string = off" (`docs.host: ""`, `s3.endpoint: ""`).
- **Secrets are referenced, never valued:** `secretName:` + `key:`, or
  `<thing>Secret: { name, key }`, or `existingSecret:` for subcharts.
- Shared hook and job images are exact-pinned in one key (`kubectlImage:`).

## `_helpers.tpl`

```yaml
{{- define "{{app}}.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Database env shared by every Python process. Params: root, db. */}}
{{- define "{{app}}.dbEnv" -}}
# DB_USER/DB_PASSWORD MUST precede {{APP}}_DATABASE_URL: Kubernetes only expands $(VAR) from
# variables defined earlier in the list.
- name: DB_USER
  value: {{ .root.Values.postgresql.auth.username | quote }}
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .root.Values.postgresql.auth.existingSecret }}
      key: password
- name: {{APP}}_DATABASE_URL
  value: "postgresql+asyncpg://$(DB_USER):$(DB_PASSWORD)@{{ .root.Release.Name }}-postgresql:5432/{{ .db }}"
{{- end -}}
```

- **Env-block helpers** are `<app>.<concern>Env` (`dbEnv`, `redisEnv`, `internalSecretEnv`,
  `s3Env`). Each takes `(dict "root" $ …params)`. There is one definition per concern, so
  identical wiring can't drift between deployments.
- **Value derivations** are helpers too (`<app>.publicOrigin`). When an empty or invalid input
  would render something plausible but broken, the helper calls `fail` with a full sentence
  explaining the consequence.

## Deployment template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{app}}-api
  labels:
    app: {{app}}-api
    {{- include "{{app}}.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.api.replicaCount }}
  # Migrates at start (image entrypoint), so two versions must never overlap.
  strategy:
    type: Recreate
  # The default of 10 hoards stale ReplicaSets.
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: {{app}}-api
  template:
    metadata:
      labels:
        app: {{app}}-api
    spec:
      imagePullSecrets:
        - name: {{ .Values.imagePullSecret }}
      containers:
        - name: {{app}}-api
          image: "{{ .Values.api.image.repository }}:{{ .Values.api.image.tag }}"
          # args, not command, so the image ENTRYPOINT (migrations) still runs.
          args: {{ .Values.api.command | toJson }}
          ports:
            - containerPort: {{ .Values.api.port }}
          env:
            - name: {{APP}}_VERSION
              value: {{ .Chart.Version | quote }}
            {{- include "{{app}}.dbEnv" (dict "root" $ "db" "{{app}}_api") | nindent 12 }}
          resources:
            {{- toYaml .Values.api.resources | nindent 12 }}
```

- **Labels.**
  - The resource gets `app: <name>` plus the shared labels.
  - The pod gets only `app`.
  - Selectors and NetworkPolicies always select on `app`.
- **`strategy: Recreate`** only for pods that migrate a schema at boot. Everything else uses
  the default rolling update.
- **No `securityContext` by default.** Web images already run as uid 1001.
- **Probes are almost never used.** Add one only where a bad rollout would be catastrophic, and
  put a comment saying so (e.g. a `tcpSocket` readiness probe on the sign-in app).
- **Resources:** requests only, no limits. Use `100m/256Mi` for APIs and `50m/128Mi` for light
  pods.
- **Service:** `type: ClusterIP`. Its name equals the Deployment name, and `port` equals the
  container port.

## Jobs, CronJobs, hooks

- **Hooks use an explicit weight ladder** and
  `"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded`:

  | Weight | When | Example |
  |---|---|---|
  | -30 | pre | install service account |
  | -25 | pre | preflight checks (`backoffLimit: 0`) |
  | -15 | pre | secret generation |
  | -5 | pre | create a missing database |
  | 5 | post | configure a dependency |
  | 10 | post | bootstrap first data (waits on `/health`) |

- **Hook scripts** are `/bin/sh -c |` blocks starting with `set -eu`. They are idempotent,
  because hooks re-run on every upgrade. Failures print an actionable message:
  `PREFLIGHT FAILED: …` plus the exact command to run.
- **CronJobs** are named `<app>-<verb>-<noun>`. They are gated on their own `enabled` *and* on
  their dependencies, and set `concurrencyPolicy: Forbid`, `successfulJobsHistoryLimit: 3`,
  `failedJobsHistoryLimit: 3` and `restartPolicy: Never`. A CronJob is singleton per fire, so it
  needs no leader election.

## Ingress (`templates/ingress.yaml`)

- The whole public surface lives in one file, with **one Ingress resource per host**, each gated
  on its host being non-empty.
- Use `ingressClassName: nginx`.
- On the app host, `/` goes to the web app and `/v1` goes straight to the API. If the web app
  proxies the API itself, the API stays cluster-internal.
- TLS (`cert-manager.io/cluster-issuer` + a `tls:` block) is gated on `certManager.enabled`.
  TLS secrets are `<app>-tls`, `<app>-<host>-tls`.

## NetworkPolicy

Each internal-only service gets one file, toggled by `<comp>.networkPolicy.enabled`, which
defaults to `true`. The comment states the invariant and that enforcement depends on the
cluster's CNI.

## Service accounts

A pod that needs an identity gets a dedicated SA with `automountServiceAccountToken: false`,
and a projected token with a specific `audience`, rather than a stored credential.

## CHANGELOG and versioning

- `CHANGELOG.md` uses Keep a Changelog: `## [Unreleased]`, then `## [X.Y.Z]` with
  `### Added / Changed / Fixed / Removed`. An optional `> ### Read before deploying` block lists
  migrations and ordering constraints.
- The section is written **in the same commit** as the `version:` bump. Publishing fails
  without it.
- **Semver:**
  - patch: image-only bumps
  - minor: template or values changes
  - major: a breaking values schema

## Validation

- Use `required "<path> is required when <x>.enabled"` and `fail "<full sentence>"` at render
  time.
- CI runs `helm lint`, then `helm template` for every supported install shape. It also asserts
  that a misconfigured render **fails**.
- `values.schema.json` only guards list-shaped declarations that need it. Put the rationale in
  `$comment`.
