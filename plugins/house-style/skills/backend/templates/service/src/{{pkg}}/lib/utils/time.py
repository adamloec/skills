"""Time helpers shared by everything that writes timestamp columns.

Every timestamp is timezone-aware UTC: in Python, in Postgres (``timestamptz``), and on the
wire (``2026-07-16T18:30:00Z``). A zone-less ISO string is ambiguous and JavaScript reads it as
local time, so ``UTCDateTime`` is the type every timestamp field uses rather than ``datetime``.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def utcnow() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Normalize any datetime to aware UTC, trusting a naive input as already UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


UTCDateTime = Annotated[datetime, AfterValidator(ensure_utc)]
"""The canonical timestamp type for every model field.

Validation accepts naive input (trusted as UTC) or aware input (converted) and always lands on
aware UTC.
"""
