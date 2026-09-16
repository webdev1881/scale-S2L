"""Каталог, журнал операций и настройки — то, чем управляет админка."""
from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import CategoryCover, Product, Transaction
from ..schemas import CategoryCoverIn, CategoryOut, ProductIn, ProductOut, TransactionOut
from ..services import live
from ..services.photos import MAX_IMAGE_BYTES, PHOTOS_DIR, cover_stem, save_photo
from ..services.settings_store import DeviceSettings, load_settings, save_settings

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/products", response_model=list[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    search: str = "",
    category: str = "",
    only_active: bool = True,
) -> list[Product]:
    stmt = select(Product)
    if only_active:
        stmt = stmt.where(Product.active == 1)
    if category:
        stmt = stmt.where(Product.category == category)
    products = list(db.scalars(stmt.order_by(Product.plu)))
    if search:
        # Фильтр по названию делается в Python: LIKE в SQLite не знает регистра кириллицы.
        needle = search.strip().lower()
        products = [
            p for p in products if needle in p.name.lower() or str(p.plu).startswith(needle)
        ]
    return products


@router.get("/products/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    """Категории собираются из товаров: отдельной таблицы групп нет.

    Обложка группы — фото первого товара в ней, чтобы не заводить второй набор
    картинок и не поддерживать его в актуальном состоянии вручную.
    """
    products = list(db.scalars(select(Product).where(Product.active == 1).order_by(Product.plu)))
    covers = {c.name: c.image for c in db.scalars(select(CategoryCover)) if c.image}
    groups: dict[str, CategoryOut] = {}
    for product in products:
        if not product.category:
            continue
        group = groups.get(product.category)
        if group is None:
            groups[product.category] = CategoryOut(
                name=product.category, image=product.image, count=1
            )
        else:
            group.count += 1
            if not group.image:
                group.image = product.image
    # Выбранная оператором обложка сильнее снимка первого товара: тот меняется
    # с каждой выгрузкой из 1С, а картинка группы должна стоять на месте.
    for group in groups.values():
        custom = covers.get(group.name)
        if custom:
            group.image = custom
            group.custom_image = True
    return sorted(groups.values(), key=lambda g: g.name)


@router.put("/products/categories/{name}/image", response_model=CategoryOut)
def set_category_image(
    name: str, payload: CategoryCoverIn, db: Session = Depends(get_db)
) -> CategoryOut:
    """Кладёт свою обложку группе. Файл ужимается так же, как снимки товаров."""
    if not db.scalar(select(Product).where(Product.category == name).limit(1)):
        raise HTTPException(404, f"Группа «{name}» не найдена")
    try:
        raw = base64.b64decode(payload.image_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(400, "Снимок не читается") from exc
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(400, f"Снимок больше {MAX_IMAGE_BYTES // (1024 * 1024)} МБ")
    try:
        filename = save_photo(cover_stem(name), raw, payload.image_format)
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc

    cover = db.get(CategoryCover, name)
    if cover is None:
        cover = CategoryCover(name=name)
        db.add(cover)
    cover.image = filename
    db.commit()
    live.notify("catalog")
    return _category_out(db, name)


@router.delete("/products/categories/{name}/image", response_model=CategoryOut)
def clear_category_image(name: str, db: Session = Depends(get_db)) -> CategoryOut:
    """Возвращает группе обложку по умолчанию — снимок первого товара."""
    cover = db.get(CategoryCover, name)
    if cover is not None:
        # Файл убираем вместе с записью: держать его дальше незачем, а имя
        # стабильно, и следующая загрузка в эту же группу создаст его заново.
        if cover.image:
            (PHOTOS_DIR / cover.image).unlink(missing_ok=True)
        db.delete(cover)
        db.commit()
        live.notify("catalog")
    return _category_out(db, name)


def _category_out(db: Session, name: str) -> CategoryOut:
    """Одна группа тем же способом, что и весь список."""
    for group in list_categories(db):
        if group.name == name:
            return group
    raise HTTPException(404, f"Группа «{name}» не найдена")


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductIn, db: Session = Depends(get_db)) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, f"PLU {payload.plu} уже занят") from exc
    db.refresh(product)
    live.notify("catalog")
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductIn, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Товар не найден")
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, f"PLU {payload.plu} уже занят") from exc
    db.refresh(product)
    live.notify("catalog")
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Товар не найден")
    # Мягкое удаление: журнал операций ссылается на товар, физическое удаление его порвёт.
    product.active = 0
    db.commit()
    live.notify("catalog")
    return {"ok": True}


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    db: Session = Depends(get_db), limit: int = Query(default=100, le=500)
) -> list[Transaction]:
    stmt = select(Transaction).order_by(Transaction.id.desc()).limit(limit)
    return list(db.scalars(stmt))


@router.get("/settings", response_model=DeviceSettings)
def get_settings_route() -> DeviceSettings:
    return load_settings()


@router.put("/settings", response_model=DeviceSettings)
def put_settings_route(payload: DeviceSettings) -> DeviceSettings:
    saved = save_settings(payload)
    live.notify("settings")
    return saved
