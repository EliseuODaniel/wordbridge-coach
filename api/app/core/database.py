"""Database configuration and session management."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


def _is_in_memory_sqlite(url: URL) -> bool:
    """Return True when the configured SQLite database is in-memory."""
    return url.drivername.startswith("sqlite") and (url.database in (None, "", ":memory:"))


def build_engine_kwargs(database_url: str) -> dict:
    """Build engine kwargs appropriate for the configured backend."""
    url = make_url(database_url)
    kwargs = {"pool_pre_ping": True}

    if url.drivername.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if _is_in_memory_sqlite(url):
            kwargs["poolclass"] = StaticPool

    return kwargs


engine = create_engine(
    settings.DATABASE_URL,
    **build_engine_kwargs(settings.DATABASE_URL),
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
