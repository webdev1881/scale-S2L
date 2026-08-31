"""Демо-каталог: без него киоск нечем показать на этапе разработки."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Product

DEMO_PRODUCTS = [
    dict(plu=101, name="Помідори чері", unit="weight", price=89.90, category="Овочі", emoji="🍅", shelf_life_days=5, image="tomato-cherry.jpg"),
    dict(plu=102, name="Огірки гладенькі", unit="weight", price=54.50, category="Овочі", emoji="🥒", shelf_life_days=7, image="cucumber.jpg"),
    dict(plu=103, name="Картопля молода", unit="weight", price=21.90, category="Овочі", emoji="🥔", shelf_life_days=30, image="potato.jpg"),
    dict(plu=104, name="Перець солодкий червоний", unit="weight", price=119.00, category="Овочі", emoji="🫑", shelf_life_days=10, image="pepper-red.jpg"),
    dict(plu=201, name="Яблука Голден", unit="weight", price=42.90, category="Фрукти", emoji="🍎", shelf_life_days=21, image="apple-golden.jpg"),
    dict(plu=202, name="Банани", unit="weight", price=48.70, category="Фрукти", emoji="🍌", shelf_life_days=7, image="banana.jpg"),
    dict(plu=203, name="Виноград Кишміш", unit="weight", price=139.00, category="Фрукти", emoji="🍇", shelf_life_days=10, image="grapes.jpg"),
    dict(plu=204, name="Мандарини", unit="weight", price=95.00, category="Фрукти", emoji="🍊", shelf_life_days=14, image="mandarin.jpg"),
    dict(plu=301, name="Філе куряче охолоджене", unit="weight", price=189.90, category="М'ясо", emoji="🍗", shelf_life_days=3, tare_g=12, image="chicken-fillet.jpg"),
    dict(plu=302, name="Фарш свинячий", unit="weight", price=229.00, category="М'ясо", emoji="🥩", shelf_life_days=2, tare_g=12, image="minced-pork.jpg"),
    dict(plu=401, name="Сир Гауда", unit="weight", price=449.00, category="Сири", emoji="🧀", shelf_life_days=30, image="cheese-gouda.jpg"),
    dict(plu=402, name="Сир Бринза", unit="weight", price=289.00, category="Сири", emoji="🧀", shelf_life_days=14, image="cheese-brynza.jpg"),
    dict(plu=501, name="Горіх волоський очищений", unit="weight", price=399.00, category="Горіхи", emoji="🌰", shelf_life_days=90, image="walnut.jpg"),
    dict(plu=502, name="Родзинки світлі", unit="weight", price=169.00, category="Горіхи", emoji="🍇", shelf_life_days=180, image="raisins.jpg"),
    dict(plu=601, name="Батон нарізний", unit="piece", price=32.50, category="Випічка", emoji="🥖", shelf_life_days=2, image="bread-loaf.jpg"),
    dict(plu=602, name="Багет французький", unit="piece", price=45.00, category="Випічка", emoji="🥖", shelf_life_days=1, image="baguette.jpg"),
]


def seed_if_empty(db: Session) -> int:
    if db.scalar(select(Product).limit(1)) is not None:
        return 0
    db.add_all(Product(**item) for item in DEMO_PRODUCTS)
    db.commit()
    return len(DEMO_PRODUCTS)
