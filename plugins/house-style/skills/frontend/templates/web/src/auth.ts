/**
 * The app's single auth import. Every RSC, server action and route handler takes its token from
 * here, so rotation has exactly one seam.
 *
 * Ships failing closed: with no session layer wired in, there is never a token, and the guarded
 * layout sends every visitor to `/login`. Wire the session layer here (Auth.js against the
 * identity provider, tokens held server-side under an opaque session cookie).
 */

/** The caller's access token, refreshed if it is about to expire, or null when signed out. */
export async function getAccessToken(): Promise<string | null> {
  return null;
}
