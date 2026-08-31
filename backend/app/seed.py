"""Демо-каталог: без него киоск нечем показать на этапе разработки."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Product

DEMO_PRODUCTS = [
    dict(plu=101, name="Помидоры черри", unit="weight", price=89.90, category="Овощи", emoji="🍅", shelf_life_days=5),
    dict(plu=102, name="Огурцы гладкие", unit="weight", price=54.50, category="Овощи", emoji="🥒", shelf_life_days=7),
    dict(plu=103, name="Картофель молодой", unit="weight", price=21.90, category="Овощи", emoji="🥔", shelf_life_days=30),
    dict(plu=104, name="Перец болгарский красный", unit="weight", price=119.00, category="Овощи", emoji="🫑", shelf_life_days=10),
    dict(plu=201, name="Яблоки Голден", unit="weight", price=42.90, category="Фрукты", emoji="🍎", shelf_life_days=21),
    dict(plu=202, name="Бананы", unit="weight", price=48.70, category="Фрукты", emoji="🍌", shelf_life_days=7),
    dict(plu=203, name="Виноград Кишмиш", unit="weight", price=139.00, category="Фрукты", emoji="🍇", shelf_life_days=10),
    dict(plu=204, name="Мандарины", unit="weight", price=95.00, category="Фрукты", emoji="🍊", shelf_life_days=14),
    dict(plu=301, name="Филе куриное охлаждённое", unit="weight", price=189.90, category="Мясо", emoji="🍗", shelf_life_days=3, tare_g=12),
    dict(plu=302, name="Фарш свиной", unit="weight", price=229.00, category="Мясо", emoji="🥩", shelf_life_days=2, tare_g=12),
    dict(plu=401, name="Сыр Гауда", unit="weight", price=449.00, category="Сыры", emoji="🧀", shelf_life_days=30),
    dict(plu=402, name="Сыр Брынза", unit="weight", price=289.00, category="Сыры", emoji="🧀", shelf_life_days=14),
    dict(plu=501, name="Орех грецкий очищенный", unit="weight", price=399.00, category="Орехи", emoji="🌰", shelf_life_days=90),
    dict(plu=502, name="Изюм светлый", unit="weight", price=169.00, category="Орехи", emoji="🍇", shelf_life_days=180),
    dict(plu=601, name="Батон нарезной", unit="piece", price=32.50, category="Выпечка", emoji="🥖", shelf_life_days=2),
    dict(plu=602, name="Багет французский", unit="piece", price=45.00, category="Выпечка", emoji="🥖", shelf_life_days=1),
]


def seed_if_empty(db: Session) -> int:
    if db.scalar(select(Product).limit(1)) is not None:
        return 0
    db.add_all(Product(**item) for item in DEMO_PRODUCTS)
    db.commit()
    return len(DEMO_PRODUCTS)
