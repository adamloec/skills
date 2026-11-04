---
name: frontend
description: House style and scaffold for frontend TypeScript — Next.js App Router (RSC + server actions as a BFF), React 19, Tailwind v4 semantic tokens, shadcn-style primitives, Zustand mirrors, pnpm. Use when starting a new web app from an app idea, or when adding or editing any page, layout, component, hook, store, server action, API client, wire type, env var or config in a frontend repo, so the folder structure, file anatomy, naming, data flow and styling match the house blueprint exactly.
when_to_use: New web app or "scaffold the frontend", add a page/route/feature/component/hook/store/server action, name a file or component, Tailwind/theming questions, tsconfig/eslint/next.config setup, shared UI or pure-logic packages.
---

# Frontend house style

This is the blueprint for every web app I build. Follow it exactly. When an existing repo
already deviates, match the repo in that file and follow this guide for anything new.

**Stack:** Next.js 16 App Router (`output: "standalone"`) · React 19 · TypeScript `strict` ·
Tailwind v4 (CSS-first, no `tailwind.config`) · shadcn-style primitives on Radix + `cva` +
`cn()` · Zustand · sonner toasts · lucide-react icons · pnpm (pinned `packageManager`) ·
ESLint flat config (`eslint-config-next`). There is no Prettier, no zod, and no React
Query/SWR until a page proves it needs one.

## Placeholders

| Token | Meaning | Example |
|---|---|---|
| `{{app}}` | short app slug, lowercase | `acme` |
| `{{App}}` | display name | `Acme` |
| `{{dist}}` | repo / package name, kebab | `acme-web` |

## Workflow

### A. New web app from an app idea

1. Copy `templates/web/` to the new repo root, including dotfiles. Substitute tokens:
   ```bash
   grep -rl '{{' . | xargs sed -i -e 's/{{dist}}/acme-web/g' -e 's/{{App}}/Acme/g' -e 's/{{app}}/acme/g'
   ```
2. The template ships one example feature, `notes`, wired end to end:
   - RSC page → `lib/api` client → server actions → client component.
   - It talks to the backend skill's template API.
   Rename it to the app's first real feature, or use it as the pattern and delete it.
3. `src/auth.ts` is the single auth seam and ships failing closed (no token, so every page
   redirects to `/login`). Wire the session layer into it (see `references/data.md`, "Auth").
4. Replace the neutral palette in `src/ui/styles/tokens.css` with the app's brand. Keep the
   token **names**.
5. Add features one at a time (`references/layout.md`, "Adding a feature").
6. `pnpm install && pnpm lint && pnpm typecheck && pnpm check:colors && pnpm build` must pass.
7. Then use the **infra** skill for the Dockerfile, CI and local compose.

Start with **one app repo**. Its `src/ui/` (design system) and `src/kit/` (pure logic and wire
types) are the in-repo stand-ins for shared packages. When a second app needs them, extract
them: see `references/packages.md`.

### B. Working in an existing repo

| Touching | Read |
|---|---|
| where a file goes, route groups, features, import boundaries | `references/layout.md` |
| any new file: directives, imports, exports, docs, formatting | `references/file-anatomy.md` |
| naming files, components, props, hooks, stores, actions, constants | `references/naming.md` |
| components, composition, Tailwind, tokens, loading/empty/error states | `references/components.md` |
| RSC reads, server actions, API client, route handlers, auth seam | `references/data.md` |
| Zustand, hydrators, URL state, cookies, context | `references/state.md` |
| wire types, unions, `interface` vs `type` | `references/types.md` |
| env vars, next.config, tsconfig, eslint, pnpm, scripts | `references/config.md` |
| shared `ui` / `kit` / server-session packages, extraction | `references/packages.md` |

## The non-negotiables

1. **The browser talks only to its own server.**
   - Reads happen in async RSC pages.
   - Writes are `"use server"` actions.
   - Route handlers exist only for streaming, downloads, OAuth callbacks and mounted auth
     handlers.
   - A client file may `import type` from `lib/api`, never import it at runtime.
2. **`app/` is routing only.** A page fetches, then renders one feature component with
   `initialX` props.
3. **Group by feature, then by type:** `features/<feature>/{actions.ts, components/, hooks/,
   lib/}`. The app's `components/` holds shell glue only.
4. **kebab-case file names everywhere.** `entity-list.tsx` exports `EntityList`. No barrels in
   the app.
5. **Named exports only.** Use default exports only where Next requires them (`page`,
   `layout`, `error`, `loading`, `not-found`, `proxy`).
6. **`function` declarations for components and module helpers.** Never write
   `const Foo = () =>`. Don't use `forwardRef`.
7. **Server actions return results and never throw:**
   `{ success: true; data } | { success: false; error }`. Every call site checks
   `result.success`.
8. **Never trust caller-supplied scope.** Actions read the token and the active scope from
   httpOnly cookies on the server.
9. **Stores are mirrors, not sources.** Zustand holds client views of server truth. They are
   seeded by renderless `*Hydrator` components from RSC props and refreshed by
   `router.refresh()`. Never use `persist`.
10. **Semantic tokens only:** `bg-card`, `text-muted-foreground`, `border-border`. No hex, no
    `dark:`, no fixed neutrals, no duration literals. `pnpm check:colors` enforces it.
11. **No parallel component library.** Primitives live in `ui` (`src/ui/` until it becomes a
    package). Feature code composes them.
12. **JSDoc on declarations, no comments in bodies.** Every module and exported symbol gets a
    `/** … */` describing the contract. TSDoc goes on every interface member.
13. **Env reads are functions evaluated at request time,** never module-scope constants. A
    module-scope read runs during `next build`, where runtime values are absent. There are no
    `NEXT_PUBLIC_*` variables: the browser gets configuration through RSC props.
14. **Unions, not enums.** Use string-literal unions, or a const object plus a same-named type.
    Use `Record<Union, X>` lookup maps so a new member is a type error until it is handled.
15. **Units in names:** `POLL_MS = 60_000`, `MAX_AGE_SECONDS`.
16. **Required data fails the page; auxiliary data degrades.** Use `notFound()` for the subject
    resource, and `Promise.allSettled` / `.catch(() => [])` for the rest.

## App shape at a glance

```
{{dist}}/
├── package.json  pnpm-lock.yaml  tsconfig.json  tsconfig.kit.json  next.config.ts
├── eslint.config.mjs  postcss.config.mjs  components.json  scripts/check-colors.mjs
└── src/
    ├── auth.ts            the one auth seam: getAccessToken()
    ├── proxy.ts           request gate (session-cookie presence) + per-request CSP
    ├── app/               routing only: (auth)/, (app)/, api/ route handlers
    ├── components/        app shell glue: providers, hydrators, layout/
    ├── features/<feature>/  actions.ts, components/, hooks/, lib/
    ├── lib/               server infrastructure: api/client.ts, api/<domain>.ts, …
    ├── stores/            cross-surface Zustand mirrors
    ├── types/             app-only types and *.d.ts shims
    ├── kit/               pure TS: wire types, formatters, error envelope (no DOM, no React)
    └── ui/                design system: components/, styles/, utils.ts (no next/*, no app imports)
```

## Before you finish

- [ ] Files are kebab-case, exports are named, and each component file matches its main export.
- [ ] Each new module and each exported symbol has JSDoc. Interface members have TSDoc. No body
      comments.
- [ ] No client file imports `lib/api` at runtime. Every write is a server action returning
      `ActionResult`.
- [ ] Only semantic tokens are used. `pnpm check:colors` passes.
- [ ] Each new env var is read inside a function, and is listed in the README's configuration
      table and in the infra wiring.
- [ ] `pnpm lint && pnpm typecheck && pnpm build` pass.
