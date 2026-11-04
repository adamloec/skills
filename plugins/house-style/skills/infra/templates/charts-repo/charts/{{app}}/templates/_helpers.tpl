{{- define "{{app}}.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Shared env blocks for the Python processes. One definition per concern, so identical wiring
cannot drift between deployments. Each takes (dict "root" $) plus the noted params.
*/}}

{{/* Database connection. Params: root, db (this service's own database). */}}
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

{{/* The web app's public origin. Fails the render on a value that would mint broken links. */}}
{{- define "{{app}}.publicOrigin" -}}
{{- if not (regexMatch "^https?://[^/]+$" .Values.appUrl) -}}
{{- fail "appUrl must be a scheme and host with no path or trailing slash (e.g. https://app.example.com). Every link and redirect the API builds starts with it." -}}
{{- end -}}
{{- .Values.appUrl -}}
{{- end -}}
