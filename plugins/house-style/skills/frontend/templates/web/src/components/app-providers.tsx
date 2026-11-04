"use client";

import { Toaster } from "sonner";

/** Client-side providers every page shares: toasts today; tooltips and confirm dialogs join here. */
export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <Toaster position="bottom-right" />
    </>
  );
}
