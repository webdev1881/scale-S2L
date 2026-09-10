"""Приём каталога из 1С по HTTPS: полная синхронизация плюс необязательные снимки.

Регламентное задание 1С присылает текущий срез каталога целиком — товар,
отсутствующий в присланном списке, гасится мягко (`active = 0`), как и при
ручной заливке `tools/import_products.py`: на него ссылается журнал операций,
удалять нельзя. Пустой список отклоняется явно, а не гасит весь каталог —
это, вероятнее, баг выгрузки на стороне 1С, а не «сегодня нет товаров».
"""
from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import Product
from ..schemas import Import1CError, Import1CRequest, Import1CResult
from ..services.photos import MAX_IMAGE_BYTES, save_product_photo

router = APIRouter(prefix="/api", tags=["1c"])


def _check_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.import_token:
        raise HTTPException(503, "Приём выгрузки из 1С не настроен (S2L_IMPORT_TOKEN пуст)")
    if authorization != f"Bearer {settings.import_token}":
        raise HTTPException(401, "Неверный или отсутствующий токен")


@router.post(
    "/catalog/1c-import",
    response_model=Import1CResult,
    dependencies=[Depends(_check_token)],
)
def import_1c(payload: Import1CRequest, db: Session = Depends(get_db)) -> Import1CResult:
    if not payload.products:
        raise HTTPException(400, "Пустой список товаров — похоже на сбой выгрузки, а не на пустой каталог")

    errors: list[Import1CError] = []
    existing = {p.plu: p for p in db.scalars(select(Product))}
    seen: set[int] = set()
    created = updated = deactivated = 0

    for item in payload.products:
        seen.add(item.plu)
        product = existing.get(item.plu)
        is_new = product is None
        was_active = bool(product.active) if product else False

        if is_new:
            product = Product(plu=item.plu, price=0.0)
            db.add(product)
            existing[item.plu] = product

        product.name = item.name
        product.unit = item.unit
        product.price = item.price
        if item.category:
            product.category = item.category
        product.active = 1 if item.in_stock else 0

        if item.image_base64 and (is_new or payload.replace_images):
            try:
                if not item.image_format:
                    raise ValueError("image_format обязателен вместе с image_base64")
                raw = base64.b64decode(item.image_base64, validate=True)
                if len(raw) > MAX_IMAGE_BYTES:
                    raise ValueError(f"снимок больше {MAX_IMAGE_BYTES // (1024 * 1024)} МБ")
                product.image = save_product_photo(item.plu, raw, item.image_format)
            except (ValueError, binascii.Error, OSError) as exc:
                errors.append(Import1CError(plu=item.plu, error=str(exc)))

        if is_new:
            created += 1
        else:
            updated += 1
            if was_active and not item.in_stock:
                deactivated += 1

    # Товары, вовсе отсутствующие в текущей выгрузке, — гасим тем же порядком.
    for plu, product in existing.items():
        if plu not in seen and product.active:
            product.active = 0
            deactivated += 1

    db.commit()

    return Import1CResult(
        received=len(payload.products),
        created=created,
        updated=updated,
        deactivated=deactivated,
        errors=errors,
    )
