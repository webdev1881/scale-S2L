"""Чистит данные прибора перед сдачей: журнал, растры этикеток, погашенные товары.

Каталог остаётся — его ведёт выгрузка из 1С. Уходит то, что накопилось при
проверке: пробные печати в журнале операций, их растры в `data/labels`, а также
товары с `active = 0`, на которые журнал больше не ссылается (погашенные
выгрузкой или тестовые). Без `--apply` только показывает, что будет удалено.

    cd backend && .venv/Scripts/python tools/clean_db.py            # план
    cd backend && .venv/Scripts/python tools/clean_db.py --apply    # почистить

На приборе — изнутри контейнера: `docker compose exec s2l python tools/clean_db.py --apply`.
Снимки в `data/photos` остаются: их перекроет следующая выгрузка, а лишние
(товар удалён) убираются тем же ключом `--apply`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import delete, select, text

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.config import LABELS_DIR, PHOTOS_DIR  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.models import CategoryCover, Product, Transaction  # noqa: E402


def main() -> int:
    apply = "--apply" in sys.argv
    with SessionLocal() as db:
        journal = db.scalar(select(text("count(*)")).select_from(Transaction)) or 0
        inactive = list(db.scalars(select(Product).where(Product.active == 0)))
        labels = [p for p in LABELS_DIR.glob("*") if p.is_file()] if LABELS_DIR.exists() else []
        # Снимки, у которых больше нет товара: имя файла — код товара. Обложки
        # групп, выбранные оператором, тоже свои — их стирать нельзя.
        known = {str(p.plu) for p in db.scalars(select(Product).where(Product.active == 1))}
        known |= {Path(c.image).stem for c in db.scalars(select(CategoryCover)) if c.image}
        stray_photos = [
            p for p in PHOTOS_DIR.glob("*") if p.is_file() and p.stem not in known
        ] if PHOTOS_DIR.exists() else []

        print(f"журнал операций: {journal} записей")
        print(f"растры этикеток: {len(labels)} файлов")
        print(f"погашенные товары: {len(inactive)}" + (
            " — " + ", ".join(f"{p.plu} {p.name}" for p in inactive[:8]) + (" …" if len(inactive) > 8 else "")
            if inactive else ""))
        print(f"снимки без товара: {len(stray_photos)}" + (
            " — " + ", ".join(p.name for p in stray_photos[:8]) + (" …" if len(stray_photos) > 8 else "")
            if stray_photos else ""))

        if not apply:
            print("\nзапуск без --apply, ничего не удалено")
            return 0

        # Журнал уходит целиком, поэтому погашенные товары больше никто не держит.
        db.execute(delete(Transaction))
        for product in inactive:
            db.delete(product)
        db.commit()

    for path in labels + stray_photos:
        path.unlink()
    with engine.connect() as conn:
        conn.execute(text("VACUUM"))
    print("\nготово: журнал и растры очищены, погашенные товары и лишние снимки удалены")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
