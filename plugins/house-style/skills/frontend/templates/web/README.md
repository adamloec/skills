# {{App}} Web

One paragraph: what this app is for, and that it talks to the API only through server actions
and RSC fetches — the browser never calls the API directly.

## Layout

```
src/
  auth.ts        the one auth seam (getAccessToken)
  proxy.ts       session-cookie gate + per-request CSP
  app/           routing only: (auth)/, (app)/, api/
  components/    app shell glue: providers, hydrators, layout/
  features/      one folder per feature: actions.ts, components/, hooks/, lib/
  lib/           server infrastructure: api/client.ts, api/<domain>.ts
  stores/        cross-surface Zustand mirrors
  kit/           pure TS: wire types, formatters, error envelope (no DOM, no React)
  ui/            design system: components/, styles/, utils.ts
```

## Running locally

```bash
pnpm install
pnpm dev          # http://localhost:3000, expects the API on http://localhost:8000
```

## Configuration

Server-only, read at request time. No `NEXT_PUBLIC_*`.

| Variable | Default | Purpose |
|---|---|---|
| `API_URL` | `http://localhost:8000` | The API's base URL. |

## Checks

```bash
pnpm lint && pnpm typecheck && pnpm check:colors && pnpm build
```
