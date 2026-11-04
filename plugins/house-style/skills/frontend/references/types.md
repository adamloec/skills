# Types

- **`interface` for object shapes. `type` for unions, aliases, mapped and derived types.**
- **No TS `enum`.** Use one of:
  - a string-literal union (the norm):
    `export type NoteStatus = "draft" | "published" | "archived";`
  - a const object plus a same-named type, when you need runtime values:
    ```ts
    export const Permission = { NOTES_READ: "notes:read", NOTES_WRITE: "notes:write" } as const;
    export type Permission = (typeof Permission)[keyof typeof Permission];
    ```
- **Exhaustive lookup maps:** `const STATUS_LABEL: Record<NoteStatus, string> = {…}`. Adding a
  member is then a compile error until it is handled. Prefer this over a `switch` in JSX.
- Use `as const` for literal config objects and inline narrowing. `satisfies` is not used.
- **No runtime validation library.**
  - Wire data is typed at the boundary: `res.json() as Promise<T>`.
  - Untrusted shapes are narrowed by hand, e.g. `typeof body.message === "string"`, or a
    `parseX(data: unknown): X | null` function.
  - A type over an upstream you don't own declares **only the fields the UI reads**.
- **Wire types live in `kit/types/<domain>.ts`**, one file per backend domain. Each opens with
  a module doc saying what it mirrors. Wire fields keep the backend's **snake_case**. Money is a
  decimal string ("parse before doing math"). Timestamps are ISO-8601 UTC strings.
- **App-only types** (view models, form state) live in `types/<domain>.ts` or a feature's
  `types.ts`, with camelCase fields.
- **Component prop contracts live with the component.**
- **Derive, don't duplicate:**
  - `Awaited<ReturnType<typeof notesApi.list>>`
  - `(typeof TABS)[number]["id"]`
  - `Pick<Note, "id" | "display_name">`
  - `Extract<Spec, { kind: "x" }>`
- **Use discriminated unions for UI modes:**
  `type PanelState = { mode: "closed" } | { mode: "edit"; id: string }`.
- **Escape hatches:**
  - `any`: never.
  - `@ts-expect-error -- reason`: last resort.
  - Non-null `!`: only right after a check the compiler cannot see.
