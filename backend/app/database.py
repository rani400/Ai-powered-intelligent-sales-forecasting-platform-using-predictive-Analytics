"""Database engine, session factory and declarative base.

Supports PostgreSQL (production target) and SQLite (local development and automated tests)
through the single ``DATABASE_URL`` environment variable.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def _build_engine() -> Engine:
    """Create the SQLAlchemy engine with engine-appropriate options."""
    if settings.is_sqlite:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            future=True,
        )

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


engine = _build_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session that is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Create all tables directly from the models (used for tests and first run)."""
    from app import models  # noqa: F401  (ensures models are registered on the metadata)

    Base.metadata.create_all(bind=engine)


def reset_database() -> None:
    """Drop and recreate every table. Used by the test suite and local resets."""
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
