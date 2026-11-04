/**
 * The result every server action returns, and the one wrapper that produces it.
 *
 * A plain server module, not a `"use server"` file: exporting `withToken` from an actions file
 * would publish it as a callable server action. Actions import both from here, so neither is
 * ever redefined.
 */

import { getAccessToken } from "@/auth";

/** A server action's outcome: the data, or a message the UI can show. Actions never throw. */
export type ActionResult<T = unknown> =
  | { success: true; data: T }
  | { success: false; error: string };

/**
 * Run `fn` with the caller's access token, turning a missing token or a thrown error into a
 * failed `ActionResult` instead of an unhandled rejection.
 *
 * @param fn - The API call to make with the token.
 * @param fallback - The message to show when the error carries none, e.g. "Failed to rename note".
 */
export async function withToken<T>(
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
