"""Приём каталога из 1С: полная синхронизация плюс необязательные снимки.

Обработка 1С (`integrations/1c/original-Libra.bsl`) присылает текущий срез
каталога целиком — товар, отсутствующий в присланном списке, гасится мягко
(`active = 0`), как и при ручной заливке `tools/import_products.py`: на него
ссылается журнал операций, удалять нельзя. Пустой список отклоняется явно, а не
гасит весь каталог — это, вероятнее, баг выгрузки на стороне 1С, а не «сегодня
нет товаров».

Формат запроса задан обработкой, а не нами: она уже работает у заказчика и
правится только по явной просьбе. Отсюда заголовок `X-API-Key`, поле `article`
вместо `plu` и позиции без артикула в пакете — всё это принимается как есть.
1С ходит на весы снаружи (через RDP на сервер 1С, дальше по интернету на адрес
магазина), поэтому токен обязателен, а пустой токен закрывает приём вовсе.
"""
from __future__ import annotations

import base64
import binascii
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import Product
from ..schemas import Import1CError, Import1CRequest, Import1CResult
from ..services import live
from ..services.photos import MAX_IMAGE_BYTES, save_product_photo

router = APIRouter(prefix="/api", tags=["1c"])

# Пять цифр кода в штрихкоде этикетки (см. services/label.py).
PLU_MAX = 99999


def _check_token(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    """Обработка 1С шлёт `X-API-Key`; `Authorization: Bearer` оставлен для curl и скриптов."""
    settings = get_settings()
    if not settings.import_token:
        raise HTTPException(503, "Приём выгрузки из 1С не настроен (S2L_IMPORT_TOKEN пуст)")
    # Пробелы по краям срезаем: токен копируют руками в поле настройки 1С или в Postman.
    presented = (x_api_key or (authorization or "").removeprefix("Bearer ")).strip()
    if not presented or not secrets.compare_digest(presented, settings.import_token.strip()):
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
        # Код товара на весах — артикул из 1С: пять цифр PLU в штрихкоде. Позиция
        # без числового артикула или с длинным кода не получит — пропускаем её и
        # говорим об этом в ответе, чтобы 1С показала это в своём логе.
        if item.plu is None:
            errors.append(Import1CError(plu=0, name=item.name, error="нет числового артикула"))
            continue
        if not 1 <= item.plu <= PLU_MAX:
            errors.append(
                Import1CError(plu=item.plu, name=item.name, error=f"артикул вне диапазона 1..{PLU_MAX}")
            )
            continue
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

    # Пакет, в котором ни одна позиция не прошла, — та же авария, что и пустой:
    # гасить по нему весь каталог нельзя.
    if not seen:
        db.rollback()
        raise HTTPException(400, "Ни у одной позиции нет пригодного артикула: " + "; ".join(e.error for e in errors[:3]))

    # Товары, вовсе отсутствующие в текущей выгрузке, — гасим тем же порядком.
    for plu, product in existing.items():
        if plu not in seen and product.active:
            product.active = 0
            deactivated += 1

    db.commit()
    live.notify("catalog")

    return Import1CResult(
        received=len(payload.products),
        created=created,
        updated=updated,
        deactivated=deactivated,
        errors=errors,
    )
