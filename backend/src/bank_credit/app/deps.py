"""Shared FastAPI dependencies."""

from datetime import UTC, datetime


def get_now() -> datetime:
    """The current time, tz-aware UTC. Tests override this dependency to control the clock."""
    return datetime.now(UTC)
