# Naming

## Files

| Thing | Convention | Example |
|---|---|---|
| Every file | **kebab-case** | `entity-gallery.tsx`, `use-auto-save.ts` |
| Component | `foo-bar.tsx` exports `FooBar` | `note-list.tsx` → `NoteList` |
| Hook | `hooks/use-<name>.ts`; `.tsx` only if it returns JSX | `use-auto-save.ts`, `use-execution-trace.tsx` |
| Store | `stores/<plural-noun>.ts`, no `-store` suffix | `stores/projects.ts` |
| Server actions | `actions.ts`, or `actions/<subject>.ts`. **Never** `*-actions.ts` | `features/notes/actions.ts` |
| API client | `lib/api/<backend-domain>.ts`, plus `client.ts` | `lib/api/notes.ts` |
| Pure helpers | `lib/<topic>.ts` | `lib/status.ts`, `lib/format.ts` |
| Wire types | `kit/types/<domain>.ts` | `kit/types/notes.ts` |
| App-only types | `types/<domain>.ts`; `types/<pkg>-<thing>.d.ts` for ambient shims | `types/canvas-view.ts` |
| Hydrator | `components/<store>-hydrator.tsx` | `projects-hydrator.tsx` |
| Scripts | `scripts/<verb>-<noun>.mjs` | `check-colors.mjs` |
| `.ts` vs `.tsx` | `.tsx` only when the file contains JSX | — |

## Code

| Kind | Convention | Example |
|---|---|---|
| Component | PascalCase `function` | `NoteList`, `PageHeader` |
| Props | `interface <Component>Props` when it is exported or large; otherwise an inline destructured type `}: { … })` | `NoteListProps` |
| Hook | `use<Thing>`, returns an object of named members | `useScopeSwitch() → { switchOrg, switching }` |
| Hook options | `interface Use<Hook>Options` | `UseAutoSaveOptions` |
| Context hook | `use<Ctx>()`, throws outside its provider | `useCanvas()` → `throw new Error("useCanvas must be used within CanvasProvider")` |
| Callback props | `on<Event>` | `onRename`, `onSaved`, `onOpenChange` |
| Local handlers | a plain verb (`save`, `toggle`, `remove`), or `handle<Event>` when it mirrors an `on<Event>` prop | — |
| Booleans | **bare adjectives and participles**: `open`, `disabled`, `busy`, `pending`, `dirty`, `hydrated`, `readOnly`; capability prefixes `can`/`has`/`needs` | `canWrite`, `hasStoredSecrets` |
| Constants | SCREAMING_SNAKE, **units in the name** | `PAGE_SIZE`, `POLL_MS = 60_000`, `MAX_AGE_SECONDS` |
| Lookup maps | `const X_LABEL: Record<Union, string>`, `X_META: Record<Union, Style>` | `STATUS_LABEL`, `KIND_META` |
| Class-string constants | SCREAMING_SNAKE | `ROW`, `COLS`, `TITLE` |
| Store state | `interface <Domain>State` | `ProjectsState` |
| Store hook | `use<Domain>Store` | `useProjectsStore` |
| Store selector | `select<Thing>(s)`, plus a `use<Thing>()` wrapper | `selectCanWrite`, `useCanWrite()` |
| Server action | **verbNoun, no `Action` suffix** | `listNotes`, `createNote`, `renameNote`, `setActiveProject` |
| Action alias at import | `<name>Action` when a store method has the same name | `import { createProject as createProjectAction }` |
| API client object | `<domain>Api`; methods take `token` first | `notesApi.list(token, { cursor })` |
| Factories | `create<Thing>()` returns a mountable thing | `createSessionGate()`, `createLogoutHandler()` |
| Wire types | PascalCase entity; **snake_case fields mirroring the backend** | `Note { display_name; is_pinned; created_at }` |
| Request bodies | `<Verb><Entity>Body` | `CreateNoteBody` |
| Pages / lists | `<Entity>Page`, `<Entity>ListItem`, `<Entity>Summary` | `NotePage` |
| View / form types | camelCase fields | `NoteForm { displayName; body }` |
| Seeded-from-server props | `initial<X>` | `initialNotes`, `initialNote` |
| Storage / event keys | `<app>:<thing>` | `"acme:chat-model"`, `"acme:notes-changed"` |
| Cookies | `<app>_<thing>`, snake_case | `acme_active_scope`, `acme_theme` |
| Route components | `<Thing>Page`, `<Thing>Layout`, `RootLayout`, `<Group>Error` | `NotesPage` |

## Env vars

These are unprefixed `SCREAMING_SNAKE`, named by concern. See `config.md`.
