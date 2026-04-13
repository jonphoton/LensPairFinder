"""Database engine and session management."""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from lenspairfinder.db.schema import Base

# Default database location: project directory
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "lenspairfinder.db"

_engine = None
_SessionFactory = None


def get_engine(db_path: Path | str | None = None):
    """Get or create the SQLAlchemy engine. Creates tables if needed."""
    global _engine
    if _engine is None:
        path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        _engine = create_engine(f"sqlite:///{path}", echo=False)
        # Enable WAL mode for better concurrent read performance
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
        Base.metadata.create_all(_engine)
    return _engine


def get_session(db_path: Path | str | None = None) -> Session:
    """Create a new database session."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine(db_path)
        _SessionFactory = sessionmaker(bind=engine)
    return _SessionFactory()


def reset_engine():
    """Reset the engine (for testing)."""
    global _engine, _SessionFactory
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
