export const metadata = { title: "Sign in" };

import { Button } from "@/ui/components/button";

/** The sign-in hand-off: one button to the identity provider's flow. */
export default function LoginPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-[18px] font-semibold tracking-[-0.01em]">Sign in to {{App}}</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">Continue with your organization account.</p>
      </div>
      <Button asChild>
        <a href="/api/auth/signin">Continue</a>
      </Button>
    </div>
  );
}
