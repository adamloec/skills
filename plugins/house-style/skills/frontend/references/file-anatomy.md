# File anatomy

## Order inside a component file

1. Directive: `"use client"` is **line 1**.
2. Imports.
3. Exported types and interfaces.
4. Module constants in SCREAMING_SNAKE: lookup maps, class strings, sizes.
5. The props `interface`, placed right above the component.
6. **The exported component.** One per file, plus at most a small exported family of
   siblings.

**There are no unexported functions or subcomponents.**
- A subcomponent gets its own kebab-case file and is exported (`note-row.tsx` → `NoteRow`).
- A pure helper with several callers goes to the feature's `lib/<topic>.ts`, or to
  `lib/`/`kit/` if it is shared across features. There it is exported and documented.
- A helper with one caller is inlined.
- A helper is never copied into a second file. Import the one definition.
- Handlers and derived values declared **inside** a component body are part of the component,
  and are fine.

```tsx
"use client";

import { useState } from "react";
import type { Note } from "@/kit/types/notes";
import { EmptyState } from "@/ui/components/empty-state";
import { NoteRow } from "./note-row";

/** Props for {@link NoteList}. */
export interface NoteListProps {
  /** Notes rendered on first paint, fetched by the page. */
  initialNotes: Note[];
}

/**
 * The notes collection: one row per note, newest first, with inline delete.
 */
export function NoteList({ initialNotes }: NoteListProps) {
  ...
}
```

## Directives

- `"use client"` is line 1, with the module JSDoc on the exported declaration below it.
- `"use server"` comes **after** the module JSDoc block:
  ```ts
  /**
   * Server actions for notes — create, rename and delete.
   *
   * Every action takes its scope from the session cookie, never from the caller, and returns
   * an `ActionResult` rather than throwing, so a failure renders inline.
   */
  "use server";
  ```
- Mark hooks and stores `"use client"` explicitly.
- A presentational leaf with no hooks or handlers carries **no directive**, so it renders on
  either side.
- Route segment config (`dynamic`, `metadata`) goes **at the top of the page, above the
  imports**:
  ```tsx
  export const dynamic = "force-dynamic";
  export const metadata = { title: "Notes" };

  import { getAccessToken } from "@/auth";
  ```
  Route handlers declare `dynamic` locally. It is never re-exported, because Next parses it
  statically.

## Imports

- **Order:**
  1. react
  2. next
  3. third-party (`lucide-react`, `sonner`, …)
  4. shared packages (`@<scope>/*`)
  5. `@/…`
  6. relative

  No blank lines between groups.
- `import type { … }` for type-only modules. Use inline `type` specifiers when a module is
  mixed: `import { relativeTime, type Note } from "@/kit/format"`.
- Use `React.ReactNode`, `React.FormEvent` and similar through the global namespace without
  importing React. `import * as React` appears only in shadcn-derived primitives.
- **Path alias:** `@/*` → `./src/*` is the only alias.

## Exports

- **Named exports everywhere.**
- Default exports only where the framework requires them:
  - Next route files: `page`, `layout`, `error`, `loading`, `not-found`
  - `proxy.ts`
  - components registered in a third-party map that wants a default
- Route components are named `<Thing>Page`, `<Thing>Layout`, `RootLayout`, `<Group>Error`,
  `Loading` and `NotFound`.
- A component file exports its main component, plus at most a small family of siblings (e.g.
  `DataTable`, `DataTableRow`, `DataTableEmpty`).
- Primitives in `ui/` derived from shadcn keep upstream's style: `function` declarations with
  an `export { … }` list at the bottom, and no semicolons. Don't "fix" them.

## Documentation

**JSDoc attaches to a declaration, never to a statement.** Nothing inside a function body gets
a comment. If a line needs explaining, give it a name.

- **Module doc:** a `/** … */` at the top, or after `"use client"`. One line when the filename
  says enough. Write a paragraph when the module is a seam: what is here and what deliberately
  is not.
- **Summary first,** imperative or descriptive, one line, ending with a period.
- **Never restate a type.** Use `@param name - meaning`, never `@param {string} name`. Write
  `@returns` only when the return needs explaining, and `@throws {ApiError}` when a caller must
  handle it.
- **Every interface member gets TSDoc.** It shows up in the consumer's editor:
  ```ts
  export interface StatTileProps {
    /** Metric name shown above the value. */
    label: string;
    /** Formatted value. The tile does no numeric formatting. */
    value: string;
    /** Period-over-period change. Positive renders green with an up arrow. */
    delta?: number;
  }
  ```
- Document the contract: null and idle behaviour, ordering, what refreshes what, failure
  mode, lifecycle ("Renders nothing.").
- **Delete on sight:**
  - comments in bodies
  - section banners (`// ---- helpers ----`, `#region`)
  - commented-out code
  - rationale paragraphs above assignments
  - restatements
  - a `TODO` with no issue link
- **Keep:**
  - `// @ts-expect-error -- reason`
  - `// eslint-disable-next-line rule -- reason`
  - `// color-guard-ignore`
  - directives
- Config files (`next.config.ts`, `.npmrc`, `pnpm-workspace.yaml`) may carry short
  why-comments next to a non-obvious setting.

## Formatting

There is no Prettier. Format by hand to these rules:

- Double quotes.
- Semicolons.
- Trailing commas in multiline lists.
- 2-space indent.
- **About 100 columns.**
- Use numeric separators for big literals: `60_000`.
- JSX attributes go on one line when they fit. Otherwise put one attribute per line with the
  closing `>` on its own line.
