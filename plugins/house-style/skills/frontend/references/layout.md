# Layout

## Repo top level

```
src/                   all code
public/                static assets
scripts/               repo scripts (.mjs): check-colors.mjs, …
tests/e2e/             end-to-end scenarios against a running stack (optional)
package.json           "packageManager": "pnpm@<exact>", scripts below
pnpm-lock.yaml
pnpm-workspace.yaml    only for allowBuilds / overrides, each with a why-comment
tsconfig.json          Next defaults + strict + "@/*" → "./src/*"
tsconfig.kit.json      the no-DOM check for src/kit
next.config.ts
eslint.config.mjs
postcss.config.mjs
components.json        shadcn aliases pointing at src/ui
Dockerfile             (infra skill)
README.md
```

## `src/`

```
src/
├── auth.ts                    the app's single auth import (getAccessToken, …)
├── proxy.ts                   Next 16 request proxy: session gate, CSP, device gate
├── app/                       ROUTING ONLY
│   ├── layout.tsx             root: theme cookie → <html> class, providers, fonts
│   ├── page.tsx               redirect("/<home>")
│   ├── not-found.tsx
│   ├── globals.css            imports ui styles, app-level @source if needed
│   ├── (auth)/                route group: unauthenticated
│   │   ├── layout.tsx
│   │   └── login/page.tsx
│   ├── (app)/                 route group: authenticated; the guard lives in its layout
│   │   ├── layout.tsx         auth guard, hydrators, shell
│   │   ├── loading.tsx        one loading boundary for the group
│   │   ├── error.tsx          one error boundary: retry or go home, never a dead end
│   │   ├── <feature>/page.tsx
│   │   ├── <feature>/[<entity>Id]/page.tsx
│   │   └── settings/{layout.tsx, page.tsx, <panel>/page.tsx}   a real route per panel
│   └── api/                   route handlers only where an action cannot do the job
│       ├── auth/[...nextauth]/route.ts
│       └── streams/[<id>]/route.ts
├── components/                APP SHELL ONLY
│   ├── app-providers.tsx      toaster, tooltip, confirm providers
│   ├── <store>-hydrator.tsx   renderless RSC → store seeders
│   └── layout/                app-shell.tsx, nav, switchers
├── features/
│   └── <feature>/
│       ├── actions.ts         "use server"; or actions/<subject>.ts when large
│       ├── components/        <feature>-<thing>.tsx; nest by sub-surface when it grows
│       ├── hooks/             use-<thing>.ts
│       ├── lib/               pure helpers, label maps, status maps
│       ├── stores/            rare: a store only this feature uses
│       └── types.ts           rare: feature-local view/form types
├── lib/                       SERVER/APP INFRASTRUCTURE ONLY
│   ├── api/client.ts          the fetch wrapper (token + scope headers, throws ApiError)
│   ├── api/<domain>.ts        one typed client object per backend domain
│   └── <topic>.ts             nav-config.ts, origin.ts, sse-relay.ts, …
├── stores/                    cross-surface Zustand mirrors: <noun>.ts
├── types/                     app-only types; <pkg>-<thing>.d.ts shims
├── kit/                       PURE LOGIC (future shared package)
│   ├── types/<domain>.ts      wire types mirroring the backend
│   ├── errors.ts              ApiError + apiError(status, body)
│   └── format.ts              formatters with injected `now`
└── ui/                        DESIGN SYSTEM (future shared package)
    ├── components/            button.tsx, page-header.tsx, empty-state.tsx, …
    ├── styles/                globals.css (Tailwind + theme mapping), tokens.css (palette)
    └── utils.ts               cn()
```

## Rules

- **`app/` holds routing files only:** `page`, `layout`, `route`, `loading`, `error` and
  `not-found`. A page is a thin async RSC. It reads the token and scope, fetches through
  `@/lib/api/*`, and renders **one** feature component with props. A route-private client
  component may sit next to its page (`app/(auth)/select-org/select-org.tsx`), but that is
  rare.
- **Group by feature first, then by type.** Every feature has the same inner shape.
- **Multiple modes.** When the app has more than one surface (e.g. "build" vs "operate"), add
  one level: `features/<mode>/<feature>`, plus `features/global/<feature>` for code both modes
  use, and `features/<mode>/shared/` for code shared inside one mode. Routes follow the modes:
  `app/(app)/<mode>/<feature>/`.
- **`components/`** holds the shell only: providers, hydrators, bridges, gates and `layout/*`.
  Never put a feature's UI there.
- **`lib/`** holds server and app infrastructure. Pure, framework-free logic goes to `kit/`.
  Drawing goes to `ui/`.
- **Import boundaries (ESLint `no-restricted-imports`):**
  - `ui/**` must not import `next/*`, `@/features`, `@/lib`, `@/stores` or `@/components`.
    Routing is injected (`linkComponent={Link}`).
  - `kit/**` must not import React, `next/*` or anything outside `kit/`. Its tsconfig has no DOM
    and no Node types.
  - One mode's features must not import another mode's. Shared code moves to `global/`.
  - `components/`, `lib/` and `stores/` must not import mode features.
- **Relative imports inside a feature, `@/` everywhere else.** `../lib/status` inside
  `features/notes` is fine. Anything crossing a feature boundary or reaching a root folder
  uses `@/…`.
- **No `index.ts` barrels in the app.** Import the file. Barrels exist only as the entry point
  of an extracted package.

## Small apps

An app with one surface and a handful of screens may keep a flat folder per concern
(`src/flow/{executor.ts, types.ts, use-flow.ts, flow-screen.tsx, stages/}`). Switch to
`features/` as soon as there is a second surface.

## Adding a feature (checklist)

For a feature `invoices`:

1. `kit/types/invoices.ts`: wire types `Invoice`, `InvoicePage`, `CreateInvoiceBody`, with
   snake_case fields mirroring the API.
2. `lib/api/invoices.ts`: `export const invoicesApi = { list, get, create, update, delete }`.
   Every method takes `token` first.
3. `features/invoices/actions.ts`: `"use server"`, `ActionResult`, `withToken`, then
   `createInvoice`, `updateInvoice`, `deleteInvoice`. Each calls `revalidatePath`.
4. `features/invoices/components/invoice-list.tsx` (client), plus any `invoice-*.tsx`
   pieces.
5. `app/(app)/invoices/page.tsx`: `dynamic = "force-dynamic"`, `metadata`, fetch, render
   `<InvoiceList initialInvoices={…} />`.
6. Add the route to the nav config. If other surfaces read the data, add a store and a
   hydrator (`state.md`).
