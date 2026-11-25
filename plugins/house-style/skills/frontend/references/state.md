# State

## Where each kind of state lives

| Kind | Home | Example |
|---|---|---|
| Session and tokens | server only; the cookie holds an opaque id | `getAccessToken()` |
| Active scope (org/project/workspace) | **one httpOnly cookie, written only by server actions**, never in the URL | `acme_active_scope = "<org>:<project>"` |
| Theme, time zone | cookies read on the server before first paint | `acme_theme` |
| Identity | RSC → React context via a bridge component | `useAuth()` |
| Cross-surface server data | Zustand **mirror** created per request with the RSC's values already in it; no `persist` | `stores/projects.ts` |
| Cross-surface UI state | Zustand | `stores/chat.ts` (open, expanded) |
| Shareable view state: filters, range, tab, drill-in | **URL search params**, read in the RSC so they reach the query | `?range=7d&status=open` |
| Per-page server data | `useState(initialX)`, refreshed through actions | `NoteList` |
| Editor-local complex state | React Context + composed hooks | `CanvasProvider` / `useCanvas()` |
| Per-browser preference that changes what is drawn | a **cookie** the layout reads, written by a store action | `acme_sidebar`, `acme_chat_model` |
| Per-person preference too large for a cookie | the **server**, read by the layout with everything else | chat's tool selection |
| Same-tab cross-component signal | `window` CustomEvent bus in `lib/events.ts` | `notifyNotesChanged()` / `onNotesChanged(fn) → unsubscribe` |

There is no global client cache. If refetching becomes expensive, the next step is React Query
or SWR, not a bigger store.

## The first paint is the real one

Anything the first paint draws is in place before anything renders, on the server and in the
browser. This is the rule the rest of this page follows.

- **Never fill a store from an effect.** A module-level `create()` store starts empty and is
  filled after mount, so the server's HTML and the first client paint are both drawn from the
  empty state: a reload shows "no projects" or a default sidebar for a moment, then corrects
  itself. A module-level store is also one object shared by every request the server renders.
- **Never restore a preference after mount.** `localStorage` cannot be read on the server, so a
  preference kept there is always drawn wrong first. If it changes what is drawn, it is a
  cookie. If it is too large for a cookie, the server keeps it.
- **Do not patch a reader.** A `hydrated` or `ready` flag on one component hides the flash in
  that component and leaves the next one broken. When two flashes of one kind turn up, fix the
  store, not the readers.

## Zustand store shape

A store that mirrors server data is created inside a provider, from a seed the layout has
already resolved. This is what Zustand prescribes for Next.js: `createStore` plus context, and
no global store.

`stores/seeded-store.tsx` holds the mechanism once:

```tsx
"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { createStore, useStore, type StateCreator, type StoreApi } from "zustand";
import { shallow } from "zustand/shallow";

/** What `seededStore` hands back: the provider that makes the store, and the hooks that read it. */
export interface SeededStore<State, Seed> {
  /** Creates the store from `seed` for everything inside it, and takes each newer seed the server sends. */
  Provider: (props: { seed: Seed; children: ReactNode }) => ReactNode;
  /** Read the store reactively. Pass an atomic selector. */
  useStore: <T = State>(selector?: (state: State) => T) => T;
  /** The store itself, for an imperative read inside a callback. */
  useStoreApi: () => StoreApi<State>;
}

/**
 * Build a store that exists per request and holds its first state before anything renders.
 *
 * @param name - Names the store in the error a hook raises outside its provider.
 * @param build - Builds the whole state from the seed: the seed's own keys, plus any actions.
 * @param take - What a newer seed changes, given the store as it is. Omit to write the seed's
 * keys over the store's. A store that saves something of its own passes this, so a seed read
 * while a save was in flight does not put the old value back.
 */
export function seededStore<State extends Seed, Seed extends object>(
  name: string,
  build: (seed: Seed) => StateCreator<State>,
  take: (state: State, seed: Seed) => Partial<State> = (_state, seed) => seed as Partial<State>,
): SeededStore<State, Seed> {
  const Context = createContext<StoreApi<State> | null>(null);

  function Provider({ seed, children }: { seed: Seed; children: ReactNode }) {
    const [store] = useState(() => createStore<State>()(build(seed)));
    const taken = useRef(seed);
    useEffect(() => {
      if (shallow(taken.current, seed)) return;
      taken.current = seed;
      store.setState(take(store.getState(), seed));
    });
    return <Context.Provider value={store}>{children}</Context.Provider>;
  }

  function useStoreApi(): StoreApi<State> {
    const store = useContext(Context);
    if (!store) throw new Error(`The ${name} store was read outside its provider.`);
    return store;
  }

  function useSeededStore<T = State>(selector?: (state: State) => T): T {
    return useStore(useStoreApi(), selector ?? ((state) => state as unknown as T));
  }

  return { Provider, useStore: useSeededStore, useStoreApi };
}
```

The first seed never goes through an effect. The effect only takes a *newer* seed, which is
what a `router.refresh()` produces by re-rendering the layout.

A store is then its seed, its state, and three exports:

```ts
"use client";

import type { Project } from "@/kit/types/projects";
import { setActiveProject as setActiveProjectAction } from "@/features/projects/actions";
import { seededStore } from "./seeded-store";

/** What the server resolves for the store. */
export interface ProjectsSeed {
  /** Every project the caller can see. */
  projects: Project[];
  /** The active project, or null when none is. */
  activeId: string | null;
}

/** Client mirror of the caller's projects and the active one. The server is the source. */
export interface ProjectsState extends ProjectsSeed {
  /** The last action's failure, shown inline by the switcher. */
  error: string | null;
  /** Switch the active project through the server, returning whether it took. */
  setActive: (projectId: string) => Promise<boolean>;
}

const store = seededStore<ProjectsState, ProjectsSeed>("projects", (seed) => (set) => ({
  ...seed,
  error: null,
  setActive: async (projectId) => {
    const result = await setActiveProjectAction(projectId);
    if (!result.success) {
      set({ error: result.error });
      return false;
    }
    set({ activeId: projectId, error: null });
    return true;
  },
}));

/** Creates the projects store for the app shell. */
export const ProjectsStoreProvider = store.Provider;

/** Read the projects store. */
export const useProjectsStore = store.useStore;

/** The projects store itself, for an imperative read inside a callback. */
export const useProjectsStoreApi = store.useStoreApi;

/** Whether the active project is set. */
export function selectHasActive(s: ProjectsState): boolean {
  return s.activeId !== null;
}
```

**Rules:**

- A store has **no `hydrate` action and no `hydrated` flag**. It is never empty, so there is
  nothing to wait for.
- The seed and the state are two exported interfaces, `<Domain>Seed` and `<Domain>State`, and
  **every member has TSDoc**.
- An async action calls a server action, sets `error` on failure, and returns a `boolean` or
  `T | null`. It never throws.
- **Consumers use atomic selectors:** `useProjectsStore((s) => s.activeId)`. Never read the
  whole store. Inside callbacks, imperative reads use `useProjectsStoreApi().getState()`.
- Hoist stable empty fallbacks (`const EMPTY: Note[] = []`) so selectors stay referentially
  stable.
- A one-shot value is consumed by a `claim<X>()` action that returns it and clears it, so a
  double-invoked effect can't send it twice.
- Purely client UI state that no server value seeds, such as a queue of unsent messages, may
  still be a module-level `create()` store. It has no first paint to get wrong.

## Seeding the stores

One client component composes every provider. The authenticated layout resolves the seeds and
renders it around the shell. The subtree is **keyed on the active scope**, so a scope change
remounts everything with fresh stores instead of hand-resetting per-component state:

```tsx
"use client";

/** Creates the app's shared stores with what the server resolved already in them. */
export function AppStores({ projects, activeId, sidebar, children }: AppStoresProps) {
  return (
    <ProjectsStoreProvider seed={{ projects, activeId }}>
      <SidebarStoreProvider seed={sidebar}>{children}</SidebarStoreProvider>
    </ProjectsStoreProvider>
  );
}
```

```tsx
<AppStores key={`${orgId}:${projectId}`} projects={projects} activeId={projectId} sidebar={sidebar}>
  <AppShell>{children}</AppShell>
</AppStores>
```

## Preferences

A preference that changes what is drawn lives in a cookie, read by the layout and handed to a
store as its seed. The store's setter writes the cookie:

```ts
setCollapsed: (collapsed) => {
  set({ collapsed });
  writePreferenceCookie(SIDEBAR_COOKIE, collapsed ? "1" : "0");
},
```

Cookie names and their parsers live in `lib/preferences.ts`, shared by the layout and the
stores. Keep the value small: a flag, an id, a short JSON object.

A preference too large for a cookie is kept on the server, per person, behind its own API, and
the layout reads it with the rest. `localStorage` is left for what the first paint never draws,
such as an unsent draft, and is read through `useSyncExternalStore`.

A layout is not given the address it renders for. When it must resolve something from the
address, such as what is open beside the page, the request gate sets the path and query on a
request header and the layout reads that.

## URL state

- Filters, ranges, tabs, selected rows and drill-ins go in search params. The RSC reads them so
  they reach the backend query.
- On the client, write them with `router.push(`${pathname}?${next}`)`, or `replace` for a
  refinement that shouldn't add history.
- **Scope never goes in the URL.** When leaving a scope, `router.replace(sectionRoot)` drops
  scope-bound params so Back never returns to a cross-scope URL.
