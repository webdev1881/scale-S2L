"""Снимки, приходящие извне (сейчас — выгрузка из 1С), а не с диска.

Приводим их к тем же правилам, что и ручной `tools/shrink_photos.py`: кадр
2427x2427 из товароучёта распаковывается в 24 МБ пикселей ради миниатюры,
и на J6412 это пропущенные кадры ровно тогда, когда покупатель листает каталог.

Файл кладётся в `data/photos` (см. `PHOTOS_DIR`), и раздаётся оттуда прежде
сборки фронта (`main.py`): демо-снимки из репозитория остаются в `dist/products`,
боевые перекрывают их по имени и живут в томе данных прибора — сборка внутри
образа при обновлении переписывается, том нет. Раньше файл шёл в `dist` и
`public` и пропадал вместе с контейнером.
"""
from __future__ import annotations

import io

from PIL import Image, ImageOps

from ..config import PHOTOS_DIR

MAX_SIDE = 800
QUALITY = 82
# Сырой base64-payload одного снимка. С запасом на несжатый кадр из товароучёта.
MAX_IMAGE_BYTES = 15 * 1024 * 1024

_EXT = {"jpg": ".jpg", "jpeg": ".jpg", "png": ".png", "webp": ".webp"}


def save_product_photo(plu: int, raw: bytes, fmt: str) -> str:
    """Ужимает и сохраняет снимок товара, возвращает имя файла для поля `image`."""
    ext = _EXT.get(fmt.lower())
    if ext is None:
        raise ValueError(f"неизвестный формат снимка: {fmt}")

    with Image.open(io.BytesIO(raw)) as image:
        # Поворот из EXIF применяем сразу: после ужатия его негде будет взять.
        image = ImageOps.exif_transpose(image)
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        # RGBA в JPEG не кладётся, а прозрачность на карточке всё равно закрыта фоном плашки.
        if ext == ".jpg" and image.mode != "RGB":
            image = image.convert("RGB")

        filename = f"{plu}{ext}"
        PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

        save_kwargs = {"optimize": True} if ext == ".png" else {"quality": QUALITY, "optimize": True}
        image.save(PHOTOS_DIR / filename, **save_kwargs)

    # Прежний файл того же товара в другом расширении больше не актуален — иначе
    # оба лежат рядом, и какой из них покажется на карточке, решает сортировка.
    for other_ext in set(_EXT.values()) - {ext}:
        (PHOTOS_DIR / f"{plu}{other_ext}").unlink(missing_ok=True)

    return filename
