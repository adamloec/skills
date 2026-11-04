/**
 * Note wire types. Mirrors the API's note model and its keyset page; fields stay snake_case.
 */

/** One note, exactly as the API returns it. */
export interface Note {
  /** Note id (UUID). */
  id: string;
  /** Owning organization. */
  org_id: string;
  /** Human label, unique within the organization. */
  display_name: string;
  /** Markdown content. */
  body: string;
  /** Pinned notes list first. */
  is_pinned: boolean;
  /** ISO-8601 UTC creation time. */
  created_at: string;
  /** ISO-8601 UTC last-change time. */
  updated_at: string;
}

/** One page of notes, newest first. */
export interface NotePage {
  /** The page's notes. */
  items: Note[];
  /** Pass back as `cursor` for the next page. Null on the last page. */
  next_cursor: string | null;
}

/** Body of a note create. Every other field is the server's to set. */
export interface CreateNoteBody {
  /** Human label. Trimmed by the server; blank is refused. */
  display_name: string;
  /** Markdown content. Defaults to empty. */
  body?: string;
}
