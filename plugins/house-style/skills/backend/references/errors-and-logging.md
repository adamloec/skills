# Errors and logging

## Exception hierarchy (`lib/exceptions/`)

```
lib/exceptions/
  __init__.py        facade + __all__
  base.py            <App>Exception
  http.py            BadRequestError 400, UnauthenticatedError 401, AuthorizationError 403,
                     NotFoundError 404, ConflictError 409, UpstreamError 502
  serialization.py   to_envelope(exc) / from_envelope(body)
  <domain>.py        domain families that carry extra context, e.g. billing.py
```

```python
class LedgerException(Exception):
    """Base for every app-defined exception.

    Attributes:
        code: Stable wire identifier. Subclasses override it, and it never changes for one.
        status_code: The HTTP status the API layer responds with.
        message: A natural-language sentence, readable by a person or an agent.
        context: Structured fields a programmatic caller would inspect.
        hint: An optional next step for whoever hit this.
        is_retryable: Whether retrying the same input could help.
    """

    code: ClassVar[str] = "ledger_error"
    status_code: ClassVar[int] = 500
    default_message: ClassVar[str] = "Something went wrong."
```

```python
class ConflictError(LedgerException):
    code: ClassVar[str] = "conflict"
    status_code: ClassVar[int] = 409
    default_message: ClassVar[str] = "Resource conflict."
```

**Rules:**

- **There is one root.** Subclasses only override the ClassVars (`code`, `status_code`,
  `default_message`). A domain family adds typed context fields in its `__init__`.
- **`code` is a stable snake_case identifier.** Clients switch on it, so never rename one.
- Services, repositories and workers raise **only** these. `HTTPException` appears only in
  routes and deps, for transport and request-shape checks.
- **The message is a sentence a person can act on:** "A note named 'Inbox' already exists".
  Put ids in `context`, not just in the message.
- `UpstreamError` (502, retryable by default) reports a failed sibling service or vendor, so
  callers can tell our bug from theirs.
- Don't leak internals. Re-raise with `from None` when the cause would expose SQL, a stack or a
  secret.
- An SDK or client package keeps its own parallel hierarchy (`<App>ClientError` →
  `NotFoundError`, …) parsed from the envelope, so raw HTTP-library errors never reach callers.

## Mapping to HTTP (`api/middleware/exception_handler.py`)

```python
async def app_exception_handler(request: Request, exc: LedgerException) -> JSONResponse:
    """Serialize any app exception into the uniform wire envelope."""
    logger.error(
        exc.message, code=exc.code, status_code=exc.status_code,
        path=request.url.path, method=request.method,
    )
    return JSONResponse(status_code=exc.status_code, content=to_envelope(exc))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log an unexpected exception and answer 500 without leaking its detail."""
    logger.exception("Unhandled exception", path=request.url.path, method=request.method)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

## Logging

- **structlog**, configured once by `setup_logging(debug=...)` in `config.py`. Debug mode uses
  the console renderer. Everywhere else the output is JSON on stdout.
- **One logger per module:** `logger = get_logger("<area>.<module>")`, placed after imports and
  constants.
- **The event is a constant sentence. The data are kwargs.** Never use an f-string or `%` in a
  log message:
  ```python
  logger.info("Invoice sent", invoice_id=str(invoice.id), org_id=invoice.org_id)
  logger.warning("Spend counter update failed", execution_id=str(run.id), error=str(e))
  ```
- **Levels:**
  - `info` for lifecycle events and state changes
  - `warning` for a degraded but handled condition
  - `error` for a typed failure returned to a caller
  - `exception` only inside `except` at a boundary
  - `debug` rarely
- Lifecycle logs bracket startup and shutdown.
- Convert UUIDs to `str` in log fields. Never log secrets, tokens or request bodies.
