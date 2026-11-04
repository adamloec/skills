"use client";

import { useState, useTransition } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { relativeTime } from "@/kit/format";
import type { Note } from "@/kit/types/notes";
import { Button } from "@/ui/components/button";
import { EmptyState } from "@/ui/components/empty-state";
import { PageHeader } from "@/ui/components/page-header";
import { cn } from "@/ui/utils";
import { deleteNote } from "../actions";
import { CreateNoteForm } from "./create-note-form";

const ROW = "grid grid-cols-[minmax(0,1fr)_96px_32px] items-center gap-3 px-4 py-2.5";

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

/** One note row. Its pending state is its own, so only the acted-on row shows it. */
function NoteRow({ note, onDeleted }: { note: Note; onDeleted: (id: string) => void }) {
  const [pending, startTransition] = useTransition();

  const remove = () => {
    startTransition(async () => {
      const result = await deleteNote(note.id);
      if (!result.success) {
        toast.error(result.error);
        return;
      }
      onDeleted(note.id);
      toast.success("Note deleted");
    });
  };

  return (
    <li className={cn(ROW, pending && "opacity-60")}>
      <span className="truncate text-[13px] font-medium">{note.display_name}</span>
      <span className="text-[12px] tabular-nums text-muted-foreground" suppressHydrationWarning>
        {relativeTime(note.created_at)}
      </span>
      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        aria-label={`Delete ${note.display_name}`}
        disabled={pending}
        onClick={remove}
      >
        <Trash2 />
      </Button>
    </li>
  );
}
