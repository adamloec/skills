import { apiError } from "@/kit/errors";
import { apiUrl } from "@/lib/env";

/** Options for one API call. */
export interface RequestOptions {
  /** HTTP method. Defaults to GET. */
  method?: string;
  /** JSON-serializable body. Omitted from the request when undefined. */
  body?: unknown;
  /** Extra headers, merged over the defaults. */
  headers?: Record<string, string>;
}

/**
 * The API client. Every method takes the caller's access token.
 *
 * Server-only: RSC pages, server actions and route handlers call this; a client component never
 * does. The active scope, once the app has one, is attached in `request` from its httpOnly
 * cookie and nowhere else.
 */
export const api = {
  /**
   * Call the API. A 204 resolves to `undefined`; any other non-2xx throws `ApiError`.
   *
   * @param path - Path under `/v1`, with the API's trailing slash on collections.
   * @param token - The caller's access token.
   * @param options - Method, body and extra headers.
   */
  async request<T>(path: string, token: string, options: RequestOptions = {}): Promise<T> {
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
  },

  get: <T>(path: string, token: string) => api.request<T>(path, token),
  post: <T>(path: string, token: string, body?: unknown) =>
    api.request<T>(path, token, { method: "POST", body }),
  patch: <T>(path: string, token: string, body?: unknown) =>
    api.request<T>(path, token, { method: "PATCH", body }),
  delete: <T>(path: string, token: string) => api.request<T>(path, token, { method: "DELETE" }),
};
