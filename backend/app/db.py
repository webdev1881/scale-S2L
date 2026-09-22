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
    _add_missing_columns()


# Колонки, добавленные к уже существующим таблицам. `create_all` их не заводит —
# он создаёт только недостающие таблицы, — а на приборе база живёт с первого дня
# и пересоздавать её нельзя: в ней каталог и журнал. Пока таких правок единицы,
# держим их списком здесь; когда станет больше — Alembic.
_ADDED_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("category_covers", "sort_order", "INTEGER"),
)


def _add_missing_columns() -> None:
    if not settings.db_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        for table, column, kind in _ADDED_COLUMNS:
            rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            if not rows or any(row[1] == column for row in rows):
                continue
            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {kind}")


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
