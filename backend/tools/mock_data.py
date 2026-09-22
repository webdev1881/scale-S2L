"""Убирает рабочую базу разработки в «мок» и возвращает обратно.

Нужно, когда в живую базу заливают каталог из 1С: выгрузка — полная синхронизация,
она гасит всё, чего нет в пакете. Чтобы демо-каталог и настройки не смешались с
боевыми, они на время переезжают в `backend/data/mock/`, а прибор начинает с
пустой базы — как новый. Снимки не трогаем: присланные из 1С лежат в
`data/photos` и просто перекрывают демо-набор из сборки по коду товара.

    cd backend && .venv/Scripts/python tools/mock_data.py stash     # убрать в мок
    cd backend && .venv/Scripts/python tools/mock_data.py restore   # вернуть

Оба действия делаются при остановленном бэкенде: SQLite-файл занят, пока uvicorn
работает, и на Windows его не переименовать. Демо-посев при пустой базе выключается
переменной `S2L_SEED_DEMO=0` в `backend/.env`, иначе на старте вместо пустого
каталога снова появится демо.
"""

from __future__ import annotations

import shutil
import sys
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
DATA = BACKEND / "data"
MOCK = DATA / "mock"

DB = DATA / "s2l.db"
SETTINGS = DATA / "settings.json"


def backend_running() -> bool:
    try:
        return urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=1).status == 200
    except Exception:  # noqa: BLE001 — не отвечает, значит остановлен
        return False


def stash() -> None:
    if (MOCK / DB.name).exists():
        sys.exit(f"мок уже занят: {MOCK / DB.name} — сначала restore, иначе снимок пропадёт")
    MOCK.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        shutil.move(str(DB), str(MOCK / DB.name))
        print(f"база     -> {MOCK / DB.name}")
    if SETTINGS.exists():
        shutil.copy2(SETTINGS, MOCK / SETTINGS.name)
        print(f"настройки скопированы в {MOCK / SETTINGS.name} (живые остаются)")
    print("живая база пуста: на старте бэкенд создаст новую (S2L_SEED_DEMO=0, чтобы без демо)")


def restore() -> None:
    if not (MOCK / DB.name).exists():
        sys.exit(f"в моке нет базы: {MOCK / DB.name}")
    shutil.move(str(MOCK / DB.name), str(DB))
    print(f"база     <- {DB}")
    if (MOCK / SETTINGS.name).exists():
        shutil.move(str(MOCK / SETTINGS.name), str(SETTINGS))
        print(f"настройки <- {SETTINGS}")
    print("мок пуст, живые данные на месте")


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action not in {"stash", "restore"}:
        print(__doc__)
        return 2
    if backend_running():
        print("бэкенд отвечает на :8000 — остановите его, база занята", file=sys.stderr)
        return 1
    stash() if action == "stash" else restore()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
