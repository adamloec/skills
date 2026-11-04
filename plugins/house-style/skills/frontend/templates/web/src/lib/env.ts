/**
 * Every environment variable the server reads, one function each.
 *
 * Functions, not constants: a module-scope `process.env` read runs during `next build`, where
 * runtime values are absent, so each value is read when it is needed. Server-only; the browser
 * receives configuration as RSC props.
 */

/** The API's base URL. Defaults to the local dev rig's API. */
export function apiUrl(): string {
  return process.env.API_URL ?? "http://localhost:8000";
}
