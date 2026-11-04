"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/nav-config";
import { cn } from "@/ui/utils";

/** The authenticated chrome: a navigation rail and the page beside it. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-screen">
      <nav
        aria-label="Sections"
        className="flex w-52 shrink-0 flex-col gap-0.5 border-r border-border/60 bg-card px-2 py-4"
      >
        <span className="px-3 pb-4 text-[14px] font-semibold tracking-[-0.01em]">{{App}}</span>
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-1.5 text-[13px] text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                active && "bg-accent text-foreground",
              )}
            >
              <item.icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
