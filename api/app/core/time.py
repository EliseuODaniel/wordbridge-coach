"""Time helpers for consistent UTC handling across the backend."""

from datetime import date, datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime for existing DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_today() -> date:
    """Return today's UTC date."""
    return datetime.now(timezone.utc).date()
