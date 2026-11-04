"use client";

import { useState, useTransition } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import type { Note } from "@/kit/types/notes";
import { Button } from "@/ui/components/button";
import { Input } from "@/ui/components/input";
import { createNote } from "../actions";

/** Inline create: a name field and a submit button. Clears itself on success. */
export function CreateNoteForm({ onCreated }: { onCreated: (note: Note) => void }) {
  const [name, setName] = useState("");
  const [pending, startTransition] = useTransition();

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    startTransition(async () => {
      const result = await createNote(name);
      if (!result.success) {
        toast.error(result.error);
        return;
      }
      setName("");
      onCreated(result.data);
      toast.success("Note created");
    });
  };

  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <Input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="New note"
        aria-label="Note name"
        className="w-56"
      />
      <Button type="submit" disabled={pending || !name.trim()}>
        <Plus />
        Add
      </Button>
    </form>
  );
}
