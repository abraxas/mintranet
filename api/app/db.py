"""SQLite persistence. The database file is intended to sit on LUKS."""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _engine_url() -> str:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{settings.db_path}"


engine = create_engine(
    _engine_url(),
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

_ready = False


def init_db() -> None:
    global _ready
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ready = True


def ensure_db() -> None:
    if not _ready:
        init_db()
