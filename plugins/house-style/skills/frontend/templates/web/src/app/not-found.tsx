import Link from "next/link";
import { Button } from "@/ui/components/button";

/** The app-wide 404: says so plainly and offers the way home. */
export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <p className="text-[14px] font-medium">This page does not exist.</p>
      <Button asChild variant="outline" size="sm">
        <Link href="/">Go home</Link>
      </Button>
    </div>
  );
}
