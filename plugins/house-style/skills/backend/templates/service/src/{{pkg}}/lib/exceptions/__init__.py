"""Typed exceptions — the single home for everything raised across a boundary.

Every exception carries a stable ``code``, an HTTP ``status_code``, a natural-language
``message``, structured ``context``, an optional ``hint`` and an ``is_retryable`` flag, and
serializes to one envelope.
"""

from {{pkg}}.lib.exceptions.base import {{App}}Exception
from {{pkg}}.lib.exceptions.http import (
    AuthorizationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthenticatedError,
    UpstreamError,
)
from {{pkg}}.lib.exceptions.serialization import from_envelope, to_envelope

__all__ = [
    "AuthorizationError",
    "BadRequestError",
    "ConflictError",
    "NotFoundError",
    "UnauthenticatedError",
    "UpstreamError",
    "{{App}}Exception",
    "from_envelope",
    "to_envelope",
]
