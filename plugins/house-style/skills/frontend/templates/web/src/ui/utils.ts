import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge class names, letting a later Tailwind utility override an earlier conflicting one. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
