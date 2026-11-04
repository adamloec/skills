"""HTTP-layer exceptions: request shape, identity, permission, lookup, conflict, upstream.

Each maps to one HTTP status and serializes to the same wire envelope.
"""

from typing import ClassVar

from {{pkg}}.lib.exceptions.base import {{App}}Exception


class BadRequestError({{App}}Exception):
    """The request is malformed in a way the handler had to parse to discover.

    Distinct from FastAPI's 422, raised before the handler runs for a mistyped parameter.
    """

    code: ClassVar[str] = "bad_request"
    status_code: ClassVar[int] = 400
    default_message: ClassVar[str] = "Malformed request."


class UnauthenticatedError({{App}}Exception):
    """The request carried no valid identity."""

    code: ClassVar[str] = "unauthenticated"
    status_code: ClassVar[int] = 401
    default_message: ClassVar[str] = "Not authenticated."


class AuthorizationError({{App}}Exception):
    """The identity is known but lacks permission."""

    code: ClassVar[str] = "authorization"
    status_code: ClassVar[int] = 403
    default_message: ClassVar[str] = "Not authorized."


class NotFoundError({{App}}Exception):
    """The resource does not exist, or is not visible to the caller."""

    code: ClassVar[str] = "not_found"
    status_code: ClassVar[int] = 404
    default_message: ClassVar[str] = "Resource not found."


class ConflictError({{App}}Exception):
    """The write collides with existing state, such as a unique name."""

    code: ClassVar[str] = "conflict"
    status_code: ClassVar[int] = 409
    default_message: ClassVar[str] = "Resource conflict."


class UpstreamError({{App}}Exception):
    """A dependency the request delegates to failed.

    Distinct from a 500 so callers can tell our bug from an upstream's. Retryable by default.
    """

    code: ClassVar[str] = "upstream"
    status_code: ClassVar[int] = 502
    default_message: ClassVar[str] = "An upstream service failed."

    def __init__(self, message: str | None = None, **kwargs) -> None:
        kwargs.setdefault("is_retryable", True)
        super().__init__(message, **kwargs)
