# Components

## Shape

- **Always `function` declarations.** Never `const Foo = () =>`, never `forwardRef` (React 19
  passes `ref` as a prop). Use `memo` only where a third-party renderer needs it.
- **Destructure props in the signature, with defaults inline:**
  `({ intervalMs = 8000, readOnly = false })`.
- Inside a component, handlers may be `const save = async () => {…}` or `function save()`.
- **Server components by default.**
  - Pages and layouts are async RSCs.
  - Interactive components are `"use client"`.
  - Presentational leaves with no hooks get no directive.
- **RSC → client handoff.** The page fetches. The client component takes `initialX`, seeds
  `useState(initialX)`, and refreshes through server actions:
  ```tsx
  const [notes, setNotes] = useState(initialNotes);
  const refresh = async () => {
    const result = await listNotes();
    if (result.success) setNotes(result.data);
    else toast.error(result.error);
  };
  ```
- **Inject server actions as props** when one shared component serves several entities. The
  component declares the structural contract it needs:
  ```tsx
  type ActionResult = { success: boolean; error?: string };
  export interface EntityActions {
    /** Rename one entity. */
    rename: (id: string, name: string) => Promise<ActionResult>;
    /** Delete one entity. */
    remove: (id: string) => Promise<ActionResult>;
  }
  ```

## Composition

- **Named `ReactNode` slot props**, not render props:
  `PageHeader({ title, description, action, controls })`.
- **Compound families for primitives:** `DataTable`, `DataTableHeader`, `DataTableRow`,
  `DataTableEmpty`.
- **`asChild`** (Radix Slot) projects styling onto a `Link`, so navigation stays a real anchor.
- **ui never imports `next/*`.** Routing is injected: `linkComponent={Link}`.
- **Renderless components** return `null` and say so ("Renders nothing."). Hydrators,
  auto-refresh and providers that only subscribe are renderless.
- **Hooks may own UI.** A hook can return `{ open, modal }`, where `modal: ReactNode`, so
  callers get the behaviour and its surface together.
- **One funnel per cross-cutting transition.** Examples: one hook for every scope switch, one
  `apiError()` reader of the error envelope, one reducer per event stream.

## The design system

- **There is no parallel component library in the app.** Primitives and shared visuals live in
  `ui/`. Feature code composes them. Page headers are always `PageHeader` (or `DetailHeader`),
  never hand-rolled.
- **ui primitive anatomy** (shadcn new-york lineage):
  - `cva` variants
  - `data-slot="<name>"` on the root
  - `data-variant` / `data-size` attributes
  - `cn(variants({ variant, size, className }))`
  - `asChild` via `Slot.Root`
- **Status taxonomy stays with the caller.** ui takes a style object
  (`{ label, dot, text, spin? }`). The app maps its own union to it with
  `Record<Status, StatusStyle>`.

## Styling (Tailwind v4)

- **Semantic tokens only:**
  - `bg-background`, `bg-card`, `bg-muted`, `bg-accent`, `bg-primary`
  - `text-foreground`, `text-muted-foreground`, `text-destructive`
  - `border-border`, `ring-ring`
  - state tokens: `bg-warning/15`, `text-success`
- **Vary tone with opacity modifiers on tokens:** `text-muted-foreground/60`,
  `border-border/60`.
- **Banned** (enforced by `scripts/check-colors.mjs`):
  - arbitrary hex (`bg-[#111]`)
  - the `dark:` variant (tokens carry the theme; `dark:` tracks the OS, not the app toggle)
  - fixed dark neutrals (`bg-zinc-900`)
  - solid `bg-black` (only `bg-black/NN` scrims are allowed)
  - white-alpha overlays (`bg-white/5`)

  The escape hatch, `// color-guard-ignore`, is rare and must be justified.
- **No motion literals.** Don't write `duration-200` or `ease-[cubic-bezier…]`. Use the named
  tokens and animations defined in `ui/styles`.
- **Type scale:** pixel-exact arbitrary sizes are the norm (`text-[13px]`, `text-[12px]`,
  `text-[11px]`). Headings get `tracking-[-0.01em]`, and figures get `tabular-nums`.
- Use `size-N` rather than `h-N w-N`.
- `cn()` is for conditional classes. Avoid template-literal classNames.
- **Responsive grids live in a constant:** `const COLS = "grid-cols-[minmax(0,1fr)_128px] md:…"`.
- **Theming:** dark-first tokens on `:root`, overridden under `.light`. The server stamps the
  class on `<html>` from a cookie before first paint. Brand colors live in
  `ui/styles/tokens.css` and nowhere else.

## States

- **Loading:**
  - One `loading.tsx` at the route-group root.
  - Pages are `force-dynamic` and await their data.
  - Don't scatter `<Suspense>`.
- **Pending stays where the action happened:** on the row or button that acted, debounced so
  it doesn't flash. Never dim the whole page. Use a full overlay only for a scope switch.
- **Error:**
  - One `error.tsx` per group that is never a dead end: it offers `reset()` ("Try again")
    and a way home. Don't auto-redirect, because a page that always throws would loop.
  - Inline errors use `role="alert"`.
  - Mutation outcomes use `toast.success` / `toast.error`.
- **Empty states distinguish two cases:**
  - *First run*: an `EmptyState` with a CTA and role-aware copy.
  - *No matches*: a "No results" line with "Clear filters".
- **Destructive actions** go through a confirm dialog (`await confirm({ title, destructive:
  true })`).
- A control that would be meaningless (a filter with one option) renders `null`, or plain text.

## Accessibility habits

- `type="button"` on every non-submit button.
- `aria-label` on icon-only buttons.
- `role="alert"` on inline errors.
- Real `<a>` (via `Link` or `asChild`) for navigation.

## Size

- Median about 80 lines. When a file passes about 300 lines, split it by sub-surface into a
  subfolder (`components/fields/`, `components/panel/`).
- Keep one component per concern. **There are no unexported subcomponents.** A piece worth
  naming gets its own exported file (`note-row.tsx`). A piece that isn't worth naming stays
  inline in the parent's JSX.
