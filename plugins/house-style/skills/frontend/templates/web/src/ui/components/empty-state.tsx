/** Props for {@link EmptyState}. */
export interface EmptyStateProps {
  /** What is missing, as a short heading. */
  title: string;
  /** What to do about it. Role-aware copy belongs here. */
  description?: string;
  /** The call to action that fills the collection. */
  action?: React.ReactNode;
}

/**
 * The first-run state of a collection: nothing exists yet, and here is how to start.
 *
 * Not for a filter that matched nothing — that is a "No results" line with "Clear filters".
 */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border/60 px-6 py-14 text-center">
      <p className="text-[14px] font-medium">{title}</p>
      {description && <p className="max-w-sm text-[13px] text-muted-foreground">{description}</p>}
      {action}
    </div>
  );
}
