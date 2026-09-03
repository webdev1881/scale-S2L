"""Привязывает снимки из frontend/public/products к товарам по имени файла.

Раскладывать полсотни карточек руками через админку — работа на вечер, поэтому
имя файла само говорит, чей это снимок: либо код товара (`101.jpg`), либо его
имя латиницей (`tomato-cherry.jpg`) — тогда сопоставление идёт по полю `image`,
которое уже стоит у товара.

    cd backend && .venv/Scripts/python tools/link_photos.py          # показать план
    cd backend && .venv/Scripts/python tools/link_photos.py --apply  # записать

Скрипт ничего не удаляет: товары, для которых снимка не нашлось, остаются как
есть, а лишние файлы просто перечисляются в конце.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.db import SessionLocal  # noqa: E402
from app.models import Product  # noqa: E402

PHOTOS = BACKEND.parent / "frontend" / "public" / "products"
SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def photo_index() -> dict[str, str]:
    """Файлы по «ключу»: имя без расширения в нижнем регистре."""
    return {
        p.stem.lower(): p.name
        for p in sorted(PHOTOS.iterdir())
        if p.is_file() and p.suffix.lower() in SUFFIXES
    }


def main() -> int:
    apply = "--apply" in sys.argv
    if not PHOTOS.is_dir():
        print(f"Каталог со снимками не найден: {PHOTOS}")
        return 1

    files = photo_index()
    used: set[str] = set()
    changes: list[tuple[Product, str]] = []
    missing: list[Product] = []

    with SessionLocal() as db:
        products = db.query(Product).filter(Product.active == 1).order_by(Product.plu).all()
        for product in products:
            # По коду товара, затем по уже записанному имени файла без расширения
            key = str(product.plu)
            found = files.get(key) or files.get(Path(product.image or "").stem.lower())
            if not found:
                missing.append(product)
                continue
            used.add(found)
            if product.image != found:
                changes.append((product, found))

        for product, name in changes:
            print(f"{product.plu:>6}  {product.name[:28]:<30} {product.image or '—'} -> {name}")
            if apply:
                product.image = name
        if apply and changes:
            db.commit()

    print(f"\nтоваров: {len(products)}, снимков: {len(files)}")
    print(f"меняется: {len(changes)}" + ("" if apply else " (запуск без --apply, ничего не записано)"))

    if missing:
        print(f"\nбез снимка ({len(missing)}):")
        for product in missing:
            print(f"{product.plu:>6}  {product.name}")

    extra = sorted(set(files.values()) - used)
    if extra:
        print(f"\nфайлы, которые никому не достались ({len(extra)}):")
        print("  " + ", ".join(extra))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
