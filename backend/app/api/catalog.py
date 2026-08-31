"""Каталог, журнал операций и настройки — то, чем управляет админка."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Product, Transaction
from ..schemas import ProductIn, ProductOut, TransactionOut
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


@router.get("/products/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)) -> list[str]:
    rows = db.scalars(select(Product.category).where(Product.active == 1).distinct())
    return sorted({r for r in rows if r})


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
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Товар не найден")
    # Мягкое удаление: журнал операций ссылается на товар, физическое удаление его порвёт.
    product.active = 0
    db.commit()
    return {"ok": True}


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    db: Session = Depends(get_db), limit: int = Query(default=100, le=500)
) -> list[Transaction]:
    stmt = select(Transaction).order_by(Transaction.id.desc()).limit(limit)
    return list(db.scalars(stmt))


@router.get("/settings", response_model=DeviceSettings)
def get_settings_route(db: Session = Depends(get_db)) -> DeviceSettings:
    return load_settings(db)


@router.put("/settings", response_model=DeviceSettings)
def put_settings_route(payload: DeviceSettings, db: Session = Depends(get_db)) -> DeviceSettings:
    return save_settings(db, payload)
