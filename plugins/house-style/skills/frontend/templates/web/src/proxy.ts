import { NextResponse, type NextRequest } from "next/server";

/** Paths reachable without a session. */
const PUBLIC_PATHS = ["/login"];

/** The session cookie the auth layer writes. Its presence is all this gate checks. */
const SESSION_COOKIE = "{{app}}_session";

/**
 * Gate every page on the presence of a session cookie, and set the per-request CSP.
 *
 * A presence check only: it never verifies or refreshes the session, so the auth layer stays the
 * single place a session is read or rotated. The guarded layout does the real check.
 */
export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  if (!isPublic && !request.cookies.has(SESSION_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  const response = NextResponse.next();
  response.headers.set("Content-Security-Policy", "frame-ancestors 'none'");
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg|api/).*)"],
};
