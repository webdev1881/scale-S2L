"""Проверка путей в конфигурации: sqlite-URL и каталог базы.

Запуск:  python backend/tests_config_paths.py

Смысл проверок — issue #2. Относительный путь в S2L_DB_URL раньше уходил в
SQLAlchemy как есть и резолвился от каталога, откуда запущен uvicorn: из
backend/ база открывалась, из корня репозитория — падала с невнятным
"unable to open database file". Расположение данных не должно зависеть от
того, откуда запущен процесс.
"""
import importlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import BASE_DIR, Settings  # noqa: E402

failed = False


def case(name: str, ok: bool, extra: str = "") -> None:
    global failed
    print(f"[{'OK ' if ok else 'FAIL'}] {name}{' — ' + extra if extra else ''}")
    if not ok:
        failed = True


expected = (BASE_DIR / "data" / "s2l.db").resolve().as_posix()

case(
    "относительный путь привязан к backend/",
    Settings(db_url="sqlite:///data/s2l.db").db_url == f"sqlite:///{expected}",
    Settings(db_url="sqlite:///data/s2l.db").db_url,
)
case(
    "путь с ./ привязан туда же",
    Settings(db_url="sqlite:///./data/s2l.db").db_url == f"sqlite:///{expected}",
)
case(
    "абсолютный unix-путь не изменён",
    Settings(db_url="sqlite:////var/lib/s2l/s2l.db").db_url == "sqlite:////var/lib/s2l/s2l.db",
)
case(
    "абсолютный windows-путь не изменён",
    Settings(db_url="sqlite:///C:/temp/s2l.db").db_url == "sqlite:///C:/temp/s2l.db",
)
case(
    "in-memory не изменён",
    Settings(db_url="sqlite:///:memory:").db_url == "sqlite:///:memory:",
)
case(
    "другая СУБД не изменена",
    Settings(db_url="postgresql+psycopg://user@host/s2l").db_url
    == "postgresql+psycopg://user@host/s2l",
)

# SQLite не создаёт недостающие каталоги — это делаем мы, иначе получается
# ровно та ошибка, с которой пришли в тикете.
with tempfile.TemporaryDirectory() as tmp:
    nested = Path(tmp) / "no" / "such" / "dir" / "s2l.db"
    os.environ["S2L_DB_URL"] = "sqlite:///" + nested.as_posix()
    try:
        import app.config as config

        config.get_settings.cache_clear()
        db = importlib.reload(importlib.import_module("app.db"))
        from sqlalchemy import text

        with db.engine.connect() as conn:
            conn.execute(text("select 1"))
        case("база открывается в несуществующем каталоге", nested.parent.is_dir())
        db.engine.dispose()
    finally:
        os.environ.pop("S2L_DB_URL", None)

print("\nИТОГ:", "есть падения" if failed else "все проверки пройдены")
sys.exit(1 if failed else 0)
