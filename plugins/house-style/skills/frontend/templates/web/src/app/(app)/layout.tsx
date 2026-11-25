import { redirect } from "next/navigation";
import { getAccessToken } from "@/auth";
import { AppShell } from "@/components/layout/app-shell";

/**
 * The authenticated group's guard and shell. No token sends the visitor to `/login`.
 *
 * Cross-surface data is resolved here once and handed to the stores as their seeds, so every
 * store holds real data before the first paint. The store composition is keyed on the active
 * scope, so a scope change remounts the tree.
 */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const token = await getAccessToken();
  if (!token) redirect("/login");
  return <AppShell>{children}</AppShell>;
}
