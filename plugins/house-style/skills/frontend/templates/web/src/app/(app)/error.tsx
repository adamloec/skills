"use client";

import Link from "next/link";
import { Button } from "@/ui/components/button";

/**
 * The authenticated group's error boundary. Never a dead end: retry the segment or go home.
 */
export default function AppError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <p className="text-[14px] font-medium">Something went wrong loading this page.</p>
      <div className="flex gap-2">
        <Button type="button" size="sm" onClick={reset}>
          Try again
        </Button>
        <Button asChild variant="outline" size="sm">
          <Link href="/">Go home</Link>
        </Button>
      </div>
    </div>
  );
}
