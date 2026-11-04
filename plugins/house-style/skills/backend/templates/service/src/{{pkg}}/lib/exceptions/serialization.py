"""Wire-envelope serialization for app exceptions.

Exceptions travel as one JSON envelope that clients parse back into a typed exception. The HTTP
status rides on the class as ``status_code``, never in the body::

    {"type": "{{app}}_error", "code": "...", "message": "...", "context": {...},
     "hint": "...", "is_retryable": false}
"""

from typing import Any

from {{pkg}}.lib.exceptions.base import {{App}}Exception
from {{pkg}}.lib.exceptions.http import (
    AuthorizationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthenticatedError,
    UpstreamError,
)

ENVELOPE_TYPE = "{{app}}_error"
"""The ``type`` every envelope carries, so a client can tell ours from a framework error."""

_CODE_TO_CLASS: dict[str, type[{{App}}Exception]] = {
    cls.code: cls
    for cls in (
        AuthorizationError,
        BadRequestError,
        ConflictError,
        NotFoundError,
        UnauthenticatedError,
        UpstreamError,
    )
}


def to_envelope(exc: {{App}}Exception) -> dict[str, Any]:
    """Serialize an exception into the wire envelope."""
    return {
        "type": ENVELOPE_TYPE,
        "code": exc.code,
        "message": exc.message,
        "context": exc.context,
        "hint": exc.hint,
        "is_retryable": exc.is_retryable,
    }


def from_envelope(body: dict[str, Any]) -> {{App}}Exception:
    """Rebuild a typed exception from an envelope, falling back to the root for unknown codes."""
    cls = _CODE_TO_CLASS.get(body.get("code", ""), {{App}}Exception)
    return cls(
        body.get("message"),
        context=body.get("context"),
        hint=body.get("hint"),
        is_retryable=bool(body.get("is_retryable", False)),
    )
