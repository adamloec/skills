# Shared packages

## One home per kind of code

| Package | Holds | Must not hold | Enforced by |
|---|---|---|---|
| **kit** (pure logic) | wire types; design tokens (the palette's source of truth); formatters; stream/event reducers; role and permission helpers; cookie *parsers*; the error envelope (`ApiError`, `apiError`); user-facing wording | DOM, React, React Native, Node globals | tsconfig `lib: ["ESNext"], types: []`; minimal deps |
| **ui** (web drawing) | React components and hooks; CSS (`styles/globals.css`, generated `tokens.css`); cookie *writers*; `EventSource` lifecycles | wire types; pure logic a native client would need; `next/*` imports (inject `Link`) | lint and review; React as a peer dep |
| **server session layer** | the auth library factory; the single token rotator; the session store and its lock; the cookie reader; mountable route handlers (`logout`, `backchannel-logout`, `session-status`); the session gate for `proxy.ts` | anything client-side; anything a credential-only origin would load | peer deps `next`, `next-auth`; `types: ["node"]` |
| app `features/global` | app-only code shared between its modes | code another repo needs | lint |

## In one repo first

A new app starts with `src/kit/` and `src/ui/` as folders in the app.

- Keep the same rules as the packages: the kit tsconfig check, and ui not importing next or
  app code.
- **No barrels yet.** Import files directly: `@/ui/components/button`, `@/kit/format`.
- The session layer starts as `src/auth.ts` plus whatever it needs under `src/lib/auth/`.

## Extracting (when a second app needs them)

1. Create `<scope>-packages` as a pnpm workspace with `packages/kit`, `packages/ui` and
   `packages/<session>`. Release them with changesets; a release is a version bump.
2. **Source-only, no build step.** `"main"`, `"types"` and the `"."` export all point at
   `./src/index.ts`. Consumers list every package in `transpilePackages`.
3. **Entry barrels:**
   - kit: `export * from "./format";` …, then `export type * from "./types/notes";`
   - ui: `export * from "./components/button";` …
   - session: explicit named re-exports grouped by module, plus one `export type { … }` block.
4. **Explicit `exports` subpaths:**
   - kit: `"./*": "./src/*.ts"`
   - ui: `"./styles"`, `"./utils"`, `"./charts"`, `"./components/*"`
   - session: one subpath per mountable handler (`"./logout"`, `"./session-gate"`)

   **A heavy or optional peer gets its own subpath** (e.g. charts), outside the root barrel.
5. Move the files and **change every consumer's import in the same change.** Leave no
   re-exports and no shims. ui does not pass kit through: a consumer imports kit's names from
   kit.
6. **Generate CSS tokens from kit.** `kit/src/tokens.ts` is the palette. `pnpm --filter ui
   tokens` writes `ui/src/styles/tokens.css`, and CI fails when they drift.
7. Route segment config (`dynamic`) is declared in each consumer's route file and never
   exported from a package.

## Rules that make the split work

- **Split pure halves from effectful halves.** For example, `foldStreamEvent(state, event,
  now)` lives in kit, and `useExecutionStream()` lives in ui. ui owns the `EventSource` and the
  React state, and folds through kit. Never hand-roll a second copy.
- **Inject the environment into pure code:**
  - `readCookie(cookieString, name)` takes `document.cookie` as an argument.
  - `relativeTime(iso, now = Date.now())`.
- **One types file per package** in the session layer (`types.ts`), so its data model reads in
  one place.
- **A `constants.ts` holds only true constants.** Anything that reads the environment is a
  function.
