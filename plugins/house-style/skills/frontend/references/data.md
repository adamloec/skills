# Data: reads, writes, the API client, auth

## The rule

**The browser talks only to its own server.**

| Need | Mechanism |
|---|---|
| Read for a page | async RSC page calls `lib/api/*` with the token |
| Write | `"use server"` action, returning an `ActionResult` |
| Client-side refetch | call a server action from the client |
| Streaming (SSE), file download, OAuth callback, mounted auth handlers, API-key reverse proxy | route handler under `app/api/` (or `app/v1/[...path]`) |

A `"use client"` file may `import type` from `lib/api`, never import it at runtime.

## The API client (`lib/api/client.ts`)

```ts
/** The backend's base URL, read per request so a runtime value reaches a prebuilt image. */
function apiUrl(): string {
  return process.env.API_URL ?? "http://localhost:8000";
}

/**
 * Call the backend with the caller's token and the request's active scope.
 *
 * A 204 resolves to `undefined`; any other non-2xx throws `ApiError`.
 */
async function request<T>(path: string, token: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers = {} } = options;
  const res = await fetch(`${apiUrl()}/v1${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) throw apiError(res.status, await res.json().catch(() => null));
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** The backend client. Every method takes the caller's access token. */
export const api = {
  get: <T>(path: string, token: string) => request<T>(path, token),
  post: <T>(path: string, token: string, body?: unknown) =>
    request<T>(path, token, { method: "POST", body }),
  patch: <T>(path: string, token: string, body?: unknown) =>
    request<T>(path, token, { method: "PATCH", body }),
  delete: <T>(path: string, token: string) => request<T>(path, token, { method: "DELETE" }),
};
```

- Attach the active scope here, once, from the httpOnly cookie (e.g. `X-<App>-Active-Org`,
  `X-<App>-Project-Id`). Those headers are **hints**: the backend verifies them against
  membership.
- `apiError(status, body)` (in `kit/errors.ts`) reads the backend's error envelope into an
  `ApiError` with `status`, `code` and `message`. It is the one place the envelope is parsed.

**Domain clients** (`lib/api/<domain>.ts`) are plain objects of thin, typed calls:

```ts
export const notesApi = {
  /** One page of the organization's notes, newest first. */
  list: (token: string, cursor?: string) =>
    api.get<NotePage>(`/notes/${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`, token),
  create: (token: string, body: CreateNoteBody) => api.post<Note>("/notes/", token, body),
  update: (token: string, id: string, body: Partial<CreateNoteBody>) =>
    api.patch<Note>(`/notes/${id}`, token, body),
  delete: (token: string, id: string) => api.delete<void>(`/notes/${id}`, token),
};
```

Collection paths keep the backend's trailing slash. Set `skipTrailingSlashRedirect: true` in
`next.config.ts`.

## Reads in RSC pages

```tsx
export const dynamic = "force-dynamic";
export const metadata = { title: "Notes" };

import { redirect } from "next/navigation";
import { getAccessToken } from "@/auth";
import { notesApi } from "@/lib/api/notes";
import { NoteList } from "@/features/notes/components/note-list";

/** The notes collection. */
export default async function NotesPage() {
  const token = await getAccessToken();
  if (!token) redirect("/login");
  const page = await notesApi.list(token).catch(() => null);
  return <NoteList initialNotes={page?.items ?? []} />;
}
```

- Every data page sets `export const dynamic = "force-dynamic"`.
- **The subject resource is required.** A 404 calls `notFound()`:
  `if (e instanceof ApiError && e.status === 404) notFound(); throw e;`.
- **Auxiliary data degrades:** `Promise.allSettled([...])`, `.catch(() => [])` or
  `.catch(() => null)`.
- **Dedupe per request** with React `cache()`:
  `export const getMe = cache(async (token: string) => meApi.get(token));`.
- Narrow URL params defensively:
  `const tab = typeof params.tab === "string" ? params.tab : null;`.

## Writes: server actions

```ts
/**
 * Server actions for notes — create, rename and delete.
 *
 * Every action takes its scope from the session cookie, never from the caller, and returns an
 * `ActionResult` rather than throwing, so a failure renders inline instead of reaching the
 * route's error boundary.
 */
"use server";

import { revalidatePath } from "next/cache";
import { getAccessToken } from "@/auth";
import { notesApi } from "@/lib/api/notes";
import type { Note } from "@/kit/types/notes";

type ActionResult<T = unknown> =
  | { success: true; data: T }
  | { success: false; error: string };

/** Run `fn` with the caller's token, turning a missing token or a thrown error into a failure. */
async function withToken<T>(
  fn: (token: string) => Promise<T>,
  fallback: string,
): Promise<ActionResult<T>> {
  const token = await getAccessToken();
  if (!token) return { success: false, error: "Not authenticated" };
  try {
    return { success: true, data: await fn(token) };
  } catch (e) {
    return { success: false, error: e instanceof Error ? e.message : fallback };
  }
}

/** Create a note in the active organization. */
export async function createNote(displayName: string): Promise<ActionResult<Note>> {
  const result = await withToken((t) => notesApi.create(t, { display_name: displayName }), "Failed to create note");
  if (result.success) revalidatePath("/notes");
  return result;
}
```

**Rules:**

- `ActionResult` and `withToken` are defined **locally** in each `"use server"` file. A
  `"use server"` file may export only async functions and types.
- Return types are always explicit: `Promise<ActionResult<T>>`.
- Each action has its own fallback message: "Failed to rename note".
- **Never accept scope or identity as an argument.** Read them on the server.
- Call `revalidatePath("<route>")` after a successful write. If the write changes data that a
  layout hydrates into a store, the client follows with `router.refresh()`.
- **At the call site, check `result.success` every time:**
  ```tsx
  const [pending, startTransition] = useTransition();
  const create = (name: string) => {
    startTransition(async () => {
      const result = await createNote(name);
      if (!result.success) { toast.error(result.error); return; }
      setNotes((prev) => [result.data, ...prev]);
      toast.success("Note created");
    });
  };
  ```
  Use `useTransition`, or a local `busy` flag with `try … finally`. Mark fire-and-forget
  promises with `void`.
- **A mount fetch through an action** uses a cancellation flag:
  ```ts
  useEffect(() => {
    let active = true;
    void listNotes().then((r) => { if (active && r.success) setNotes(r.data); });
    return () => { active = false; };
  }, []);
  ```

## Auth

- **One seam.** `src/auth.ts` re-exports the session layer's helpers. Every RSC and action
  imports `getAccessToken` from `@/auth`, so token rotation happens in exactly one place.
- **Recommended session layer:**
  - Auth.js (`next-auth` v5) runs OIDC against the app's identity provider.
  - Tokens are kept **server-side** (e.g. Redis), keyed by an opaque session id in an httpOnly
    cookie, so nothing token-shaped reaches the browser.
  - `getAccessToken()` refreshes under a lock when the token is close to expiry.
- **`proxy.ts`** (the Next 16 request proxy) is a cookie-**presence** gate only. It asks
  whether the request names a session, redirects to `/login` when not, and sets the per-request
  CSP. It never calls the auth library and never writes.
- **The `(app)` layout is the real guard.** No token redirects to `/login`. If the identity
  provider says the user has no organization, redirect to the org picker.
- **Client identity** comes from a React context mounted by a bridge component in the root
  layout (`useAuth()`), seeded from the RSC. The client never fetches it.
- **Client role checks are UX gating only.** The backend is the hard gate. An unknown role
  stays permissive during hydration rather than hiding actions.
