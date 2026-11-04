import { redirect } from "next/navigation";

/** The root has no page of its own; it lands on the home section. */
export default function RootPage() {
  redirect("/notes");
}
