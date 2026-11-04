import type { Metadata } from "next";
import { cookies } from "next/headers";
import { AppProviders } from "@/components/app-providers";
import { THEME_COOKIE, parseTheme } from "@/kit/theme";
import "@/ui/styles/globals.css";

export const metadata: Metadata = {
  title: { template: "%s · {{App}}", default: "{{App}}" },
  description: "{{App}}.",
};

/**
 * The root shell: stamps the theme on `<html>` before first paint and mounts the providers.
 *
 * The theme is read from its cookie here, server-side, so the first paint already matches the
 * viewer's choice; an absent cookie renders the dark default.
 */
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const theme = parseTheme((await cookies()).get(THEME_COOKIE)?.value);
  return (
    <html lang="en" className={theme === "light" ? "light" : undefined}>
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
