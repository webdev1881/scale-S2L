"""Ужимает снимки товаров под размер карточки.

Карточка на экране прибора — около 300 px по ширине, а снимки приходят из
товароучёта какими есть: попадаются кадры 2427x2427. Такой файл распаковывается
в 24 МБ пикселей ради миниатюры, и на J6412 это пропущенные кадры ровно в тот
момент, когда покупатель листает каталог. Ужимаем до разумной стороны — вес и
время декодирования падают, а на экране разницы не видно.

    cd backend && .venv/Scripts/python tools/shrink_photos.py          # показать план
    cd backend && .venv/Scripts/python tools/shrink_photos.py --apply  # переписать

Ключи:
    --max=800       наибольшая сторона после ужатия (по умолчанию 800)
    --quality=82    качество JPEG и WebP

Файлы переписываются на месте — они лежат в репозитории, и откатить можно
`git checkout`. Формат сохраняется: имя файла записано у товара в поле `image`,
и менять расширение значило бы чинить ещё и базу.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

PHOTOS = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "products"
SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def arg(name: str, default: int) -> int:
    for item in sys.argv:
        if item.startswith(f"--{name}="):
            return int(item.split("=", 1)[1])
    return default


def main() -> int:
    apply = "--apply" in sys.argv
    limit = arg("max", 800)
    quality = arg("quality", 82)
    if not PHOTOS.is_dir():
        print(f"Каталог со снимками не найден: {PHOTOS}")
        return 1

    было = стало = 0
    план: list[tuple[str, str, str, int, int]] = []

    for path in sorted(PHOTOS.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        размер = path.stat().st_size
        было += размер
        with Image.open(path) as image:
            # Поворот из EXIF применяем сразу: после ужатия его негде будет взять.
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            if max(width, height) <= limit:
                стало += размер
                continue
            image.thumbnail((limit, limit), Image.LANCZOS)
            new_width, new_height = image.size
            if apply:
                if path.suffix.lower() == ".png":
                    image.save(path, optimize=True)
                else:
                    # RGBA в JPEG не кладётся, а прозрачность на карточке всё равно
                    # закрыта фоном плашки.
                    if path.suffix.lower() in (".jpg", ".jpeg") and image.mode != "RGB":
                        image = image.convert("RGB")
                    image.save(path, quality=quality, optimize=True)
                новый = path.stat().st_size
            else:
                новый = 0
        стало += новый if apply else размер // 4  # оценка: примерно четверть прежнего
        план.append(
            (
                path.name,
                f"{width}x{height}",
                f"{new_width}x{new_height}",
                round(размер / 1024),
                round(новый / 1024) if apply else 0,
            )
        )

    хвост = "" if apply else "  (запуск без --apply, ничего не переписано)"
    print(f"снимков: всего в папке {sum(1 for p in PHOTOS.iterdir() if p.suffix.lower() in SUFFIXES)}, "
          f"ужимается {len(план)}{хвост}")
    for name, before, after, kb_before, kb_after in план:
        стрелка = f" -> {kb_after} КБ" if apply else ""
        print(f"  {name:<16} {before:>11} -> {after:<9} {kb_before:>5} КБ{стрелка}")
    print(f"\nбыло {round(было / 1024 / 1024, 1)} МБ, "
          f"{'стало' if apply else 'ожидается около'} {round(стало / 1024 / 1024, 1)} МБ")
    if not apply:
        print("оценка приблизительная: точный вес известен только после пересжатия")
    else:
        print("не забудьте `npm run build` — сборка копирует снимки в dist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
