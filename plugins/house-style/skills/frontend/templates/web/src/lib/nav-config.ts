import { NotebookPen, type LucideIcon } from "lucide-react";

/** One entry in the app's navigation rail. */
export interface NavItem {
  /** Route the entry links to; also the prefix that marks it active. */
  href: string;
  /** Visible label. */
  label: string;
  /** Icon drawn beside the label. */
  icon: LucideIcon;
}

/** The navigation rail, top to bottom. */
export const NAV_ITEMS: NavItem[] = [{ href: "/notes", label: "Notes", icon: NotebookPen }];
