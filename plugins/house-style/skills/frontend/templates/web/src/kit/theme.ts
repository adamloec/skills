/**
 * The UI theme and the cookie it lives in. Dark is the default; light is a class on `<html>`.
 */

/** A UI theme. */
export type Theme = "dark" | "light";

/** Cookie the theme choice lives in, read on the server so the first paint already matches. */
export const THEME_COOKIE = "{{app}}_theme";

/** Read a theme cookie value, defaulting anything unknown to dark. */
export function parseTheme(value: string | undefined): Theme {
  return value === "light" ? "light" : "dark";
}
