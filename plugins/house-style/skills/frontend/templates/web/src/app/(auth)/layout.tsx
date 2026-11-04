/** The unauthenticated group: one centered card, no app chrome. */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm rounded-xl border border-border/60 bg-card p-8">{children}</div>
    </div>
  );
}
