/** Props for {@link PageHeader}. */
export interface PageHeaderProps {
  /** The page's title, also its `<h1>`. */
  title: string;
  /** One sentence under the title saying what the page is for. */
  description?: string;
  /** Item count shown beside the title. Omitted while unknown. */
  count?: number;
  /** The page's primary action, right-aligned. */
  action?: React.ReactNode;
}

/**
 * The header every top-level page opens with. Pages never hand-roll their own.
 */
export function PageHeader({ title, description, count, action }: PageHeaderProps) {
  return (
    <header className="flex items-start justify-between gap-6 pb-6">
      <div className="min-w-0">
        <h1 className="flex items-baseline gap-2 text-[20px] font-semibold tracking-[-0.01em]">
          {title}
          {count !== undefined && (
            <span className="text-[13px] font-normal tabular-nums text-muted-foreground">{count}</span>
          )}
        </h1>
        {description && <p className="mt-1 text-[13px] text-muted-foreground">{description}</p>}
      </div>
      {action}
    </header>
  );
}
