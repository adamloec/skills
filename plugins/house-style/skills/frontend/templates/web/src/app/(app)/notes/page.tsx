export const dynamic = "force-dynamic";
export const metadata = { title: "Notes" };

import { redirect } from "next/navigation";
import { getAccessToken } from "@/auth";
import { NoteList } from "@/features/notes/components/note-list";
import { notesApi } from "@/lib/api/notes";

/** The notes collection: fetches the first page, then hands it to the client list. */
export default async function NotesPage() {
  const token = await getAccessToken();
  if (!token) redirect("/login");
  const page = await notesApi.list(token);
  return <NoteList initialNotes={page.items} />;
}
