"use client";

import { useTransition } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { relativeTime } from "@/kit/format";
import type { Note } from "@/kit/types/notes";
import { Button } from "@/ui/components/button";
import { cn } from "@/ui/utils";
import { deleteNote } from "../actions";

/** The row grid, shared by every column so the list stays aligned. */
const ROW = "grid grid-cols-[minmax(0,1fr)_96px_32px] items-center gap-3 px-4 py-2.5";

/** Props for {@link NoteRow}. */
export interface NoteRowProps {
  /** The note this row shows. */
  note: Note;
  /** Called with the note's id once the server has deleted it. */
  onDeleted: (id: string) => void;
}

/**
 * One note in the collection, with inline delete.
 *
 * Its pending state is its own, so only the row that acted shows it.
 */
export function NoteRow({ note, onDeleted }: NoteRowProps) {
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
