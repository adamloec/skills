# Configuration, env vars and tooling

## Environment variables

- **Server-only and read at request time.** An env read is an exported **function** in
  `lib/env.ts`, never a module-scope constant. A module-scope `process.env` read runs during
  `next build`, where runtime values are absent:
  ```ts
  /** Longest a session record may live. */
  export function sessionTtlSeconds(): number {
    return Number(process.env.SESSION_TTL_SECONDS ?? 30 * 24 * 60 * 60);
  }
  ```
- **A required variable throws with an explanation** that names the variable and why it has no
  default:
  ```ts
  const url = process.env.REDIS_URL;
  if (!url) throw new Error("REDIS_URL is required — the session store has no fallback");
  ```
- **An optional variable** gets `??` and a local-dev default (`process.env.API_URL ??
  "http://localhost:8000"`).
- **There are no `NEXT_PUBLIC_*` variables.** The browser gets what it needs as RSC props, such
  as a docs URL or a version stamp read in a layout. Images stay environment-agnostic: one build
  runs in every environment.
- **Names:** unprefixed SCREAMING_SNAKE, grouped by concern.

  | Concern | Names |
  |---|---|
  | Backend | `API_URL` |
  | Auth library (Auth.js convention) | `AUTH_SECRET`, `AUTH_URL`, `AUTH_<PROVIDER>_ID`, `AUTH_<PROVIDER>_SECRET`, `AUTH_<PROVIDER>_ISSUER` |
  | Session store | `REDIS_URL`, `SESSION_TTL_SECONDS`, `SESSION_KEY_PREFIX` |
  | Links to sibling apps | `<THING>_URL` (`DOCS_URL`) |
  | Version stamp | `<APP>_VERSION`, set by the deploy, empty in dev |

  Units go in the name (`_SECONDS`, `_MS`). Each new variable is added to the README's
  configuration table and to the deployment's env wiring (infra skill).
- There is no `.env` committed. Local values come from defaults and the compose rig. An
  `.env.example` exists only when a variable has no safe default.

## `next.config.ts`

```ts
import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "geolocation=(), microphone=(), camera=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
];

const nextConfig: NextConfig = {
  output: "standalone",
  skipTrailingSlashRedirect: true,
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
```

- Use `output: "standalone"` for the image (infra skill).
- `transpilePackages` lists every source-only shared package once they exist.
- **CSP is set per request in `proxy.ts`, not here.** Headers in `next.config` are baked in at
  build time.
- Use no rewrites for the backend. A runtime route handler can honour a runtime `API_URL`; a
  build-time rewrite cannot.

## TypeScript

- **App:** the stock Next `tsconfig` with `strict: true`, `moduleResolution: "bundler"`,
  `jsx: "react-jsx"`, and `paths: { "@/*": ["./src/*"] }`. That is the only alias.
- **`tsconfig.kit.json`** checks `src/kit` with `"lib": ["ESNext"], "types": []`. A `window`,
  `document`, `EventSource` or `process` reference there is a type error.
- Shared packages: `target/module ESNext`, `strict`, `noEmit`, and **no path aliases**
  (relative imports only).

## ESLint (flat config)

- `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`.
- **Boundaries go in `no-restricted-imports`,** with a message that names the fix:
  > "ui must not import app code or next/*. Inject it as a prop."
- Rules are disabled only per line, with a reason:
  `// eslint-disable-next-line react-hooks/exhaustive-deps -- seeded once`.
- Next 16 has no `next lint`. Run `eslint .` directly.

## pnpm

- `"packageManager": "pnpm@<exact version>"` is pinned in every repo.
- `.npmrc` maps a private scope to its registry and holds **no auth line**. CI provides the
  token.
- `pnpm-workspace.yaml` exists only for `allowBuilds`, `overrides` and
  `minimumReleaseAgeExclude`. Each entry gets a why-comment.

## Scripts

```json
{
  "dev": "next dev --turbopack",
  "build": "next build",
  "start": "next start",
  "lint": "eslint .",
  "typecheck": "tsc --noEmit && tsc -p tsconfig.kit.json",
  "check:colors": "node scripts/check-colors.mjs"
}
```

CI runs `lint`, `typecheck`, `check:colors` and `build`.

## Tests

- There are no component unit tests by default. Correctness is carried by:
  - `strict` types
  - the no-DOM kit check
  - the import boundaries
  - the color guard
- **Pure logic goes in `kit/` or `lib/` precisely so it can be tested in isolation.** When tests
  are added, target those modules first: formatters, reducers, mappers.
- **End-to-end:** `tests/e2e/scenarios.mjs`, run with `pnpm test:e2e` against the running dev
  stack.
  - It is plain Node ESM with a tiny `scenario(name, fn)` / `assert(cond, msg)` runner and a
    cookie-jarred `fetch`.
  - It exercises the seams: sign-in, session lifetime, logout, an API key lifecycle.
  - A header doc lists each scenario and its prerequisites.
