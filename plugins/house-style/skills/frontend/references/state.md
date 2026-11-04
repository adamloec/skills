# State

## Where each kind of state lives

| Kind | Home | Example |
|---|---|---|
| Session and tokens | server only; the cookie holds an opaque id | `getAccessToken()` |
| Active scope (org/project/workspace) | **one httpOnly cookie, written only by server actions**, never in the URL | `acme_active_scope = "<org>:<project>"` |
| Theme, time zone | cookies read on the server before first paint | `acme_theme` |
| Identity | RSC → React context via a bridge component | `useAuth()` |
| Cross-surface server data | Zustand **mirror** hydrated from RSC; no `persist` | `stores/projects.ts` |
| Cross-surface UI state | Zustand | `stores/chat.ts` (open, expanded) |
| Shareable view state: filters, range, tab, drill-in | **URL search params**, read in the RSC so they reach the query | `?range=7d&status=open` |
| Per-page server data | `useState(initialX)`, refreshed through actions | `NoteList` |
| Editor-local complex state | React Context + composed hooks | `CanvasProvider` / `useCanvas()` |
| Per-browser preference | `localStorage` behind a store action, wrapped in `try/catch`, restored **after mount** | `useChatModel.restore()` |
| Same-tab cross-component signal | `window` CustomEvent bus in `lib/events.ts` | `notifyNotesChanged()` / `onNotesChanged(fn) → unsubscribe` |

There is no global client cache. If refetching becomes expensive, the next step is React Query
or SWR, not a bigger store.

## Zustand store shape

```ts
"use client";

import { create } from "zustand";
import type { Project } from "@/kit/types/projects";
import { setActiveProject as setActiveProjectAction } from "@/features/projects/actions";

/** Client mirror of the caller's projects and the active one. The server is the source. */
export interface ProjectsState {
  /** Every project the caller can see. */
  projects: Project[];
  /** The active project, or null before hydration. */
  activeId: string | null;
  /** True once the RSC hydrator has seeded the store. Client fetches gate on this. */
  hydrated: boolean;
  /** The last action's failure, shown inline by the switcher. */
  error: string | null;
  /** Seed from RSC props. Called by `ProjectsHydrator` only. */
  hydrate: (input: { projects: Project[]; activeId: string | null }) => void;
  /** Switch the active project through the server, returning whether it took. */
  setActive: (projectId: string) => Promise<boolean>;
}

export const useProjectsStore = create<ProjectsState>()((set) => ({
  projects: [],
  activeId: null,
  hydrated: false,
  error: null,
  hydrate: ({ projects, activeId }) => set({ projects, activeId, hydrated: true, error: null }),
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

/** Whether the active project is set. */
export function selectHasActive(s: ProjectsState): boolean {
  return s.activeId !== null;
}
```

**Rules:**

- Use the curried `create<State>()((set, get) => …)`.
- State and actions share one exported `interface <Domain>State`, and **every member has
  TSDoc**.
- An async action calls a server action, sets `error` on failure, and returns a `boolean` or
  `T | null`. It never throws.
- **Consumers use atomic selectors:** `useProjectsStore((s) => s.activeId)`. Never read the
  whole store. Inside callbacks, imperative reads use `useProjectsStore.getState()`.
- Hoist stable empty fallbacks (`const EMPTY: Note[] = []`) so selectors stay referentially
  stable.
- A one-shot value is consumed by a `claim<X>()` action that returns it and clears it, so a
  double-invoked effect can't send it twice.

## Hydrators

```tsx
"use client";

import { useEffect } from "react";
import { useProjectsStore } from "@/stores/projects";
import type { Project } from "@/kit/types/projects";

/**
 * Seeds the projects store from RSC-resolved values. Renders nothing.
 *
 * Re-fires on `router.refresh()`: the layout re-renders with fresh props, so a mutation that
 * ends in a refresh reaches every store reader without a client refetch.
 */
export function ProjectsHydrator({ projects, activeId }: { projects: Project[]; activeId: string | null }) {
  const hydrate = useProjectsStore((s) => s.hydrate);
  useEffect(() => {
    hydrate({ projects, activeId });
  }, [hydrate, projects, activeId]);
  return null;
}
```

The authenticated layout renders hydrators **before** the shell. The layout subtree is
**keyed on the active scope**, so a scope change remounts everything instead of hand-resetting
per-component state:

```tsx
<Fragment key={`${orgId}:${projectId}`}>
  <ProjectsHydrator projects={projects} activeId={projectId} />
  <AppShell>{children}</AppShell>
</Fragment>
```

## URL state

- Filters, ranges, tabs, selected rows and drill-ins go in search params. The RSC reads them so
  they reach the backend query.
- On the client, write them with `router.push(`${pathname}?${next}`)`, or `replace` for a
  refinement that shouldn't add history.
- **Scope never goes in the URL.** When leaving a scope, `router.replace(sectionRoot)` drops
  scope-bound params so Back never returns to a cross-scope URL.
