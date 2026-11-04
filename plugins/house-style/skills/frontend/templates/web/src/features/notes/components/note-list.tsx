"use client";

import { useState } from "react";
import type { Note } from "@/kit/types/notes";
import { EmptyState } from "@/ui/components/empty-state";
import { PageHeader } from "@/ui/components/page-header";
import { CreateNoteForm } from "./create-note-form";
import { NoteRow } from "./note-row";

/** Props for {@link NoteList}. */
export interface NoteListProps {
  /** Notes rendered on first paint, fetched by the page. */
  initialNotes: Note[];
}

/**
 * The notes collection: a create form, then one row per note, newest first.
 *
 * Seeded from the page's fetch and kept current from each action's result, so no mutation
 * refetches the list.
 */
export function NoteList({ initialNotes }: NoteListProps) {
  const [notes, setNotes] = useState(initialNotes);
  const created = (note: Note) => setNotes((prev) => [note, ...prev]);
  const removed = (id: string) => setNotes((prev) => prev.filter((n) => n.id !== id));

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-8">
      <PageHeader
        title="Notes"
        count={notes.length}
        description="Everything your organization has written down."
        action={<CreateNoteForm onCreated={created} />}
      />
      {notes.length === 0 ? (
        <EmptyState title="No notes yet" description="Add the first one to get started." />
      ) : (
        <ul className="divide-y divide-border/60 rounded-lg border border-border/60 bg-card">
          {notes.map((note) => (
            <NoteRow key={note.id} note={note} onDeleted={removed} />
          ))}
        </ul>
      )}
    </div>
  );
}
