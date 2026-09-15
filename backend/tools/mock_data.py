"""Убирает рабочие данные разработки в «мок» и возвращает обратно.

Нужно, когда в живую базу заливают каталог из 1С: выгрузка — полная синхронизация,
она гасит всё, чего нет в пакете, и кладёт свои снимки под теми же кодами. Чтобы
демо-каталог, настройки и снимки не смешались с боевыми, они на время переезжают
в `backend/data/mock/`, а прибор начинает с пустой базы — как новый.

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
PUBLIC_PHOTOS = BACKEND.parent / "frontend" / "public" / "products"
DIST_PHOTOS = BACKEND.parent / "frontend" / "dist" / "products"

DB = DATA / "s2l.db"
SETTINGS = DATA / "settings.json"


def backend_running() -> bool:
    try:
        return urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=1).status == 200
    except Exception:  # noqa: BLE001 — не отвечает, значит остановлен
        return False


def move_dir(src: Path, dst: Path) -> int:
    """Переносит файлы src в dst (создаёт dst), возвращает число файлов."""
    dst.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in sorted(src.iterdir()) if src.exists() else []:
        if path.is_file():
            shutil.move(str(path), str(dst / path.name))
            moved += 1
    return moved


def stash() -> None:
    if MOCK.exists() and any(MOCK.iterdir()):
        sys.exit(f"мок уже занят: {MOCK} — сначала restore, иначе снимок пропадёт")
    MOCK.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        shutil.move(str(DB), str(MOCK / DB.name))
        print(f"база     -> {MOCK / DB.name}")
    if SETTINGS.exists():
        shutil.copy2(SETTINGS, MOCK / SETTINGS.name)
        print(f"настройки скопированы в {MOCK / SETTINGS.name} (живые остаются)")
    n = move_dir(PUBLIC_PHOTOS, MOCK / "products")
    print(f"снимков  -> {MOCK / 'products'}: {n}")
    # dist — сборка, при restore пересобирается копированием из public.
    if DIST_PHOTOS.exists():
        shutil.rmtree(DIST_PHOTOS)
        DIST_PHOTOS.mkdir()
    print("живая база пуста: на старте бэкенд создаст новую (S2L_SEED_DEMO=0, чтобы без демо)")


def restore() -> None:
    if not (MOCK / DB.name).exists():
        sys.exit(f"в моке нет базы: {MOCK / DB.name}")
    shutil.move(str(MOCK / DB.name), str(DB))
    print(f"база     <- {DB}")
    if (MOCK / SETTINGS.name).exists():
        shutil.move(str(MOCK / SETTINGS.name), str(SETTINGS))
        print(f"настройки <- {SETTINGS}")
    # Снимки, которые успела прислать 1С, живому демо не нужны — убираем, чтобы код
    # товара показывал именно демо-кадр, а не боевой под тем же номером.
    for stale in PUBLIC_PHOTOS.glob("*") if PUBLIC_PHOTOS.exists() else []:
        if stale.is_file():
            stale.unlink()
    n = move_dir(MOCK / "products", PUBLIC_PHOTOS)
    print(f"снимков  <- {PUBLIC_PHOTOS}: {n}")
    if DIST_PHOTOS.parent.exists():
        if DIST_PHOTOS.exists():
            shutil.rmtree(DIST_PHOTOS)
        shutil.copytree(PUBLIC_PHOTOS, DIST_PHOTOS)
    shutil.rmtree(MOCK / "products", ignore_errors=True)
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
