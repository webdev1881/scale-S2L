"""Заливает каталог из выгрузки товароучёта `docs/prod.xlsx`.

Выгрузка из товароучёта даёт два столбца — артикул и наименование. Всё остальное
выводится из них же: артикул становится кодом товара (`plu`), по нему же находится
снимок, а единица измерения читается из названия — «... кг» весовой, «... шт» и
«... 200гр» штучные. Так каталог собирается из того, что есть, без ручной работы.

    cd backend && .venv/Scripts/python tools/import_products.py            # показать план
    cd backend && .venv/Scripts/python tools/import_products.py --apply    # записать

Ключи:
    --random-prices   поставить случайную цену там, где её нет (нулевая) — заглушка
                      до настоящей выгрузки цен; уже заполненные цены не трогает
    --groups=word     группа = первое слово названия (по умолчанию)
    --groups=single   всё в одну группу «Всі товари»
    --groups=keep     не трогать группы уже заведённых товаров

Товары, которых в выгрузке нет, гасятся мягко (`active = 0`): на них ссылается
журнал операций, и удалять их нельзя.

Файл `.xlsx` читается напрямую (zip + XML), без сторонних библиотек: разбор нужен
один раз при заливке, а прибору лишняя зависимость ни к чему.
"""

from __future__ import annotations

import random
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.db import SessionLocal  # noqa: E402
from app.models import Product  # noqa: E402

PHOTOS = BACKEND.parent / "frontend" / "public" / "products"
# Выгрузка лежит в `docs/`, а не рядом со снимками: всё, что попадает в
# `public/products`, уезжает в сборку и раздаётся прибором — список артикулов с
# наименованиями там ни к чему.
BOOK = BACKEND.parent / "docs" / "prod.xlsx"
SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Цены-заглушки: весовой товар в этом магазине дороже штучного, и разброс взят
# такой, чтобы на этикетке и в шапке числа выглядели правдоподобно.
PRICE_RANGE = {"weight": (89.0, 899.0), "piece": (19.0, 349.0)}


def read_rows(book: Path) -> list[tuple[str, str]]:
    """Строки первого листа: (артикул, наименование). Заголовок отбрасывается."""
    with zipfile.ZipFile(book) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ElementTree.fromstring(zf.read("xl/sharedStrings.xml"))
            # Строка может быть разбита на куски (<r><t>…</t></r>) — склеиваем все.
            shared = ["".join(t.text or "" for t in si.iter(f"{NS}t")) for si in root]
        sheet = ElementTree.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows: list[tuple[str, str]] = []
    for row in sheet.iter(f"{NS}row"):
        cells: dict[str, str] = {}
        for cell in row.iter(f"{NS}c"):
            column = re.sub(r"\d", "", cell.get("r", ""))
            value = cell.find(f"{NS}v")
            if cell.get("t") == "s" and value is not None:
                cells[column] = shared[int(value.text or 0)]
            elif cell.get("t") == "inlineStr":
                cells[column] = "".join(t.text or "" for t in cell.iter(f"{NS}t"))
            elif value is not None:
                cells[column] = value.text or ""
        article, name = cells.get("A", "").strip(), cells.get("B", "").strip()
        if article and name:
            rows.append((article, name))
    # Первая строка — заголовок: артикул там не число.
    return [r for r in rows if r[0].isdigit()]


def photo_index() -> dict[str, str]:
    """Снимки по артикулу. Сортировка решает споры: `.webp` перебивает `.jpg`."""
    return {
        p.stem.lower(): p.name
        for p in sorted(PHOTOS.iterdir())
        if p.is_file() and p.suffix.lower() in SUFFIXES
    }


def unit_of(name: str) -> str:
    """«... кг» — весовой, всё остальное штучное: «шт», «200гр», «8г»."""
    return "weight" if re.search(r"\bкг$", name) else "piece"


def price_for(plu: int, unit: str) -> float:
    """Цена-заглушка. Зерно — код товара: повторный запуск даёт то же число."""
    low, high = PRICE_RANGE[unit]
    return round(random.Random(plu).uniform(low, high), 1)


def group_of(name: str) -> str:
    """Первое слово названия: «Арахіс смажений» и «Арахіс солоний» встанут рядом."""
    return name.split()[0].strip(",.").capitalize()[:60]


def main() -> int:
    apply = "--apply" in sys.argv
    random_prices = "--random-prices" in sys.argv
    groups = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--groups=")), "word")
    if groups not in ("word", "single", "keep"):
        print(f"неизвестная раскладка групп: {groups}")
        return 1
    if not BOOK.is_file():
        print(f"Выгрузка не найдена: {BOOK}")
        return 1

    rows = read_rows(BOOK)
    photos = photo_index()
    новых = обновлённых = без_снимка = 0

    with SessionLocal() as db:
        существующие = {p.plu: p for p in db.query(Product).all()}
        пришедшие: set[int] = set()

        for article, name in rows:
            plu = int(article)
            пришедшие.add(plu)
            unit = unit_of(name)
            image = photos.get(article.lower(), "")
            if not image:
                без_снимка += 1

            product = существующие.get(plu)
            if product is None:
                product = Product(plu=plu, price=0.0)
                новых += 1
                if apply:
                    db.add(product)
            else:
                обновлённых += 1

            product.name = name[:120]
            product.unit = unit
            product.image = image
            product.active = 1
            if groups == "word":
                product.category = group_of(name)
            elif groups == "single":
                product.category = "Всі товари"
            # Цена ставится только там, где её нет: настоящая выгрузка цен, когда
            # она появится, не должна затираться заглушкой.
            if random_prices and not product.price:
                product.price = price_for(plu, unit)

        # Демо-каталог не удаляем: на его товары ссылается журнал операций.
        лишние = [p for plu, p in существующие.items() if plu not in пришедшие and p.active]
        for product in лишние:
            product.active = 0

        if apply:
            db.commit()

    хвост = "" if apply else "  (запуск без --apply, ничего не записано)"
    print(f"в выгрузке: {len(rows)}, снимков в папке: {len(photos)}{хвост}")
    print(f"новых: {новых}, обновлено: {обновлённых}, погашено: {len(лишние)}")
    if без_снимка:
        print(f"без снимка: {без_снимка}")
    if groups != "keep":
        сколько = len({group_of(n) for _, n in rows}) if groups == "word" else 1
        print(f"групп получилось: {сколько}")
    if random_prices:
        print("цены-заглушки проставлены там, где цены не было")
    лишние_файлы = len(set(photos) - {a for a, _ in rows})
    if лишние_файлы:
        print(f"снимков, которым не нашлось товара: {лишние_файлы}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
