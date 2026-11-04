# Env vars and secrets, end to end

## One variable, four places

A new setting is never done until it exists in all four places, in the same change:

| Place | Backend example | Web example |
|---|---|---|
| Code | `invite_ttl_days: int = 14` on the settings class | `function sessionTtlSeconds()` reading `process.env.SESSION_TTL_SECONDS` |
| README configuration table | `{{APP}}_INVITE_TTL_DAYS` | `SESSION_TTL_SECONDS` |
| Compose `environment:` | `{{APP}}_INVITE_TTL_DAYS: ${INVITE_TTL_DAYS:-14}` | `SESSION_TTL_SECONDS: ${SESSION_TTL_SECONDS:-2592000}` |
| Chart deployment `env:` | `value: {{ .Values.api.env.{{APP}}_INVITE_TTL_DAYS \| quote }}` | `value: {{ .Values.web.env.SESSION_TTL_SECONDS \| quote }}` |

## Names

- **Backend:** `{{APP}}_` + the settings field name, upper-cased. One prefix for every Python
  process of the app.
- **Web:** unprefixed SCREAMING_SNAKE, named by concern: `API_URL`, `AUTH_*`, `REDIS_URL`,
  `SESSION_*`.
- **Version stamp:** `{{APP}}_VERSION`, set by the chart from `.Chart.Version`, empty in dev.
- **Units are in the name:** `_SECONDS`, `_DAYS`, `_MS`.

## Plain values

- Always quote: `value: {{ .Values.api.env.X | quote }}`.
- Build composite values in the template from other values, rather than asking operators to
  repeat themselves: `value: "http://{{app}}-api:{{ .Values.api.port }}"`.
- **Derive instead of setting** when a mode follows from whether its infrastructure exists:
  ```yaml
  - name: {{APP}}_INVITE_EMAIL_ENABLED
    value: {{ ternary "true" "false" (not (empty .Values.smtp.host)) | quote }}
  ```
- **Gate the block on the feature:** `{{- if .Values.s3.endpoint }}` … `{{- end }}`. Empty
  means off.

## Secrets

- **Always `secretKeyRef`.** The Secret name comes from values, and the key is a kebab-case
  literal or also from values:
  ```yaml
  - name: {{APP}}_INTERNAL_SECRET
    valueFrom:
      secretKeyRef:
        name: {{ .Values.appSecrets.secretName }}
        key: internal-secret
  ```
- A late-provisioned secret is `optional: true`, so a rollout starts with the gate closed rather
  than crash-looping.
- **Compose a URL from a secret** with `$(VAR)`, declaring the parts **first**. See the `dbEnv`
  helper in `helm.md`.
- **Secret names:** `<app>-<purpose>` (`{{app}}-secrets`, `{{app}}-postgres-auth`,
  `{{app}}-s3`). **Keys** are kebab-case (`auth-secret`, `internal-secret`, `password`). Use
  env-shaped keys only when the Secret is consumed via `envFrom`.
- **How a Secret comes to exist:**
  1. `appSecrets.create: true` renders it from values, each key guarded by `required`. This is
     for dev and scratch clusters only.
  2. A pre-install/pre-upgrade generator Job creates any missing key with a random value and
     **never overwrites** an existing one. It is a Job, not a template function, because GitOps
     renders with `helm template`, where `randAlphaNum` changes on every sync.
  3. Out of band, via Terraform or an installer script. This is the only path for registry and
     cloud credentials (`ghcr-credentials`, `{{app}}-s3`).
- **Never** put a production secret in `values.yaml`, in git, or in a build arg.

## The web app sees only server-side env

There are no `NEXT_PUBLIC_*` variables. Values the browser needs (a docs URL, the version) are
read in an RSC and passed as props. That keeps the image environment-agnostic.

## Shared secrets between services

When two services must agree on a value (an internal secret, an admin secret), **one Secret key
feeds both deployments** through one helper (`{{app}}.internalSecretEnv`). The value is never
duplicated in values.
