from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .models import Base

settings = get_settings()

def _ensure_sqlite_dir(url: str) -> None:
    """SQLite не создаёт недостающие каталоги и падает с "unable to open database file"."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return
    target = url[len(prefix) :]
    if not target or target.startswith(":memory:"):
        return
    Path(target).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.db_url)

connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
engine = create_engine(settings.db_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Схема создаётся напрямую. При первом изменении моделей в проде — вводим Alembic."""
    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
