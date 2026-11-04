import { api } from "@/lib/api/client";
import type { CreateNoteBody, Note, NotePage } from "@/kit/types/notes";

/** Note routes, one thin typed call each. */
export const notesApi = {
  /** One page of the organization's notes, newest first. */
  list: (token: string, cursor?: string) =>
    api.get<NotePage>(`/notes/${cursor ? `?cursor=${encodeURIComponent(cursor)}` : ""}`, token),

  create: (token: string, body: CreateNoteBody) => api.post<Note>("/notes/", token, body),

  update: (token: string, id: string, body: Partial<CreateNoteBody>) =>
    api.patch<Note>(`/notes/${id}`, token, body),

  delete: (token: string, id: string) => api.delete<void>(`/notes/${id}`, token),
};
