/** Instant fallback for soft navigations: every page awaits its data before rendering. */
export default function Loading() {
  return (
    <div className="flex min-h-[60vh] animate-fade-in items-center justify-center text-[13px] text-muted-foreground">
      Loading…
    </div>
  );
}
