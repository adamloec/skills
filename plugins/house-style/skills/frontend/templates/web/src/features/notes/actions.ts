/**
 * Server actions for notes — list, create, rename and delete.
 *
 * Every action takes the caller's token from the session on the server, never from the caller,
 * and returns an `ActionResult` rather than throwing, so a failure renders inline instead of
 * reaching the route's error boundary.
 */
"use server";

import { revalidatePath } from "next/cache";
import type { Note } from "@/kit/types/notes";
import { type ActionResult, withToken } from "@/lib/action-result";
import { notesApi } from "@/lib/api/notes";

/** The first page of the organization's notes, newest first. */
export async function listNotes(): Promise<ActionResult<Note[]>> {
  return withToken(async (t) => (await notesApi.list(t)).items, "Failed to load notes");
}

/** Create a note in the caller's organization. */
export async function createNote(displayName: string): Promise<ActionResult<Note>> {
  const result = await withToken(
    (t) => notesApi.create(t, { display_name: displayName }),
    "Failed to create note",
  );
  if (result.success) revalidatePath("/notes");
  return result;
}

/** Rename a note. */
export async function renameNote(id: string, displayName: string): Promise<ActionResult<Note>> {
  const result = await withToken(
    (t) => notesApi.update(t, id, { display_name: displayName }),
    "Failed to rename note",
  );
  if (result.success) revalidatePath("/notes");
  return result;
}

/** Delete a note. */
export async function deleteNote(id: string): Promise<ActionResult<null>> {
  const result = await withToken(async (t) => {
    await notesApi.delete(t, id);
    return null;
  }, "Failed to delete note");
  if (result.success) revalidatePath("/notes");
  return result;
}
