"""Exception handlers that turn raised errors into wire responses."""

from fastapi import Request
from fastapi.responses import JSONResponse

from {{pkg}}.lib.exceptions import {{App}}Exception, to_envelope
from {{pkg}}.lib.utils.logger import get_logger

logger = get_logger("api.errors")


async def app_exception_handler(request: Request, exc: {{App}}Exception) -> JSONResponse:
    """Serialize any app exception into the uniform wire envelope.

    Status comes from the exception's ``status_code``; the body is the envelope clients parse
    back into a typed exception.
    """
    logger.error(
        exc.message, code=exc.code, status_code=exc.status_code,
        path=request.url.path, method=request.method,
    )
    return JSONResponse(status_code=exc.status_code, content=to_envelope(exc))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log an unexpected exception and answer 500 without leaking its detail to the caller."""
    logger.exception("Unhandled exception", path=request.url.path, method=request.method)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
