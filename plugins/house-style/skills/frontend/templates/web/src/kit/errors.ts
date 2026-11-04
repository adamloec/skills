/**
 * The API's error envelope, read once, here.
 *
 * Every non-2xx response carries `{ type, code, message, context, hint, is_retryable }`; a
 * framework error may not, so every field is narrowed by hand.
 */

/** A failed API call, with the envelope's stable `code` and readable `message`. */
export class ApiError extends Error {
  /** HTTP status of the response. */
  readonly status: number;
  /** Stable identifier from the envelope, e.g. `"not_found"`; `"http_error"` when absent. */
  readonly code: string;
  /** Whether retrying the same call could help. */
  readonly retryable: boolean;

  constructor(status: number, code: string, message: string, retryable: boolean) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryable = retryable;
  }
}

/** Build an `ApiError` from a response status and its parsed body, whatever shape it has. */
export function apiError(status: number, body: unknown): ApiError {
  const envelope = typeof body === "object" && body !== null ? (body as Record<string, unknown>) : {};
  const code = typeof envelope.code === "string" ? envelope.code : "http_error";
  const message =
    typeof envelope.message === "string"
      ? envelope.message
      : typeof envelope.detail === "string"
        ? envelope.detail
        : `Request failed (${status})`;
  return new ApiError(status, code, message, envelope.is_retryable === true);
}
