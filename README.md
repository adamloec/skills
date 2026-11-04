# adamloec — personal Claude Code plugins

A personal plugin marketplace. It currently ships one plugin, **house-style**: the blueprint
for how I build apps. Give Claude an app idea and it scaffolds the backend, the web app and the
deployment layer with the same layout, file anatomy, naming, config and code shape every time.

## Install

```text
/plugin install house-style --marketplace adamloec/skills
```

On older Claude Code versions, do it in two steps:

```text
/plugin marketplace add adamloec/skills
/plugin install house-style@adamloec
```

## What's inside

| Skill | Invoke | Covers | Template |
|---|---|---|---|
| `backend` | `/house-style:backend` | uv · FastAPI · SQLModel · Alembic · pydantic-settings · structlog · pytest. Repo and package layout, Python file anatomy, naming, functions and classes, settings and env vars, routes and deps, data layer and migrations, errors and logging, tests | `templates/service/`: a runnable API with one example resource through every layer, tests passing |
| `frontend` | `/house-style:frontend` | Next.js App Router as a BFF · React 19 · Tailwind v4 semantic tokens · Zustand mirrors · pnpm. Folder structure, file anatomy, naming, components and styling, server actions, state, types, env vars and tooling, shared packages | `templates/web/`: a runnable app with one example feature end to end; lint, typecheck, color guard and build passing |
| `infra` | `/house-style:infra` | Dockerfiles, migrate-then-exec entrypoint, docker-compose dev rig, Helm chart, env and secret wiring, CI with immutable `sha-` tags, chart releases | `templates/service/`, `templates/web/`, `templates/charts-repo/` |

The skills also load on their own whenever Claude is writing code they cover. You don't have
to invoke them by name.

## Using it

Start a new app:

> I want to build an app for tracking shared household expenses. Scaffold the backend, the web
> app and the charts repo using house-style.

Claude picks the tokens (`{{app}}`, `{{App}}`, `{{APP}}`, `{{pkg}}`, `{{dist}}`, `{{org}}`),
copies the templates, renames the example resource to your first real one, and builds out from
there one vertical at a time.

Work in an existing repo: just ask for the change. The relevant skill's references tell Claude
where the file goes, what it is called and how it is shaped.

## Layout

```
.claude-plugin/marketplace.json
plugins/house-style/
  .claude-plugin/plugin.json
  skills/
    backend/   SKILL.md  references/*.md  templates/service/
    frontend/  SKILL.md  references/*.md  templates/web/
    infra/     SKILL.md  references/*.md  templates/{service,web,charts-repo}/
```

## Developing

```bash
claude plugin validate .
claude plugin marketplace add ./      # test locally before pushing
```

Bump `plugins/house-style/.claude-plugin/plugin.json` `version` when a skill changes, so
installs pick up the update.
