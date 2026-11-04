import { apiError } from "@/kit/errors";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

/** The API's base URL, read per request so a runtime value reaches a prebuilt image. */
function apiUrl(): string {
  return process.env.API_URL ?? "http://localhost:8000";
}

/**
 * Call the API with the caller's access token.
 *
 * Server-only: RSC pages, server actions and route handlers call this; a client component never
 * does. The active scope, once the app has one, is attached here from its httpOnly cookie and
 * nowhere else. A 204 resolves to `undefined`; any other non-2xx throws `ApiError`.
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

/** The API client. Every method takes the caller's access token. */
export const api = {
  get: <T>(path: string, token: string) => request<T>(path, token),
  post: <T>(path: string, token: string, body?: unknown) =>
    request<T>(path, token, { method: "POST", body }),
  patch: <T>(path: string, token: string, body?: unknown) =>
    request<T>(path, token, { method: "PATCH", body }),
  delete: <T>(path: string, token: string) => request<T>(path, token, { method: "DELETE" }),
};
