"""Демо-каталог: без него киоск нечем показать на этапе разработки.

Групп и позиций заведомо больше, чем помещается на страницу сетки (по умолчанию
4x2), чтобы пагинация была видна и на списке групп, и внутри групп.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Product

DEMO_PRODUCTS = [
    # --- Овочі ---
    dict(plu=101, name="Помідори чері", unit="weight", price=89.90, category="Овочі", emoji="🥬", shelf_life_days=5, image="tomato-cherry.jpg"),
    dict(plu=102, name="Огірки гладенькі", unit="weight", price=54.50, category="Овочі", emoji="🥬", shelf_life_days=7, image="cucumber.jpg"),
    dict(plu=103, name="Картопля молода", unit="weight", price=21.90, category="Овочі", emoji="🥬", shelf_life_days=30, image="potato.jpg"),
    dict(plu=104, name="Перець солодкий", unit="weight", price=119.00, category="Овочі", emoji="🥬", shelf_life_days=10, image="pepper-red.jpg"),
    dict(plu=105, name="Морква", unit="weight", price=24.50, category="Овочі", emoji="🥬", shelf_life_days=30, image="carrot.jpg"),
    dict(plu=106, name="Цибуля ріпчаста", unit="weight", price=19.90, category="Овочі", emoji="🥬", shelf_life_days=60, image="onion.jpg"),
    dict(plu=107, name="Капуста білоголова", unit="weight", price=16.90, category="Овочі", emoji="🥬", shelf_life_days=30, image="cabbage.jpg"),
    dict(plu=108, name="Буряк столовий", unit="weight", price=18.50, category="Овочі", emoji="🥬", shelf_life_days=45, image="beetroot.jpg"),
    dict(plu=109, name="Кабачки", unit="weight", price=46.00, category="Овочі", emoji="🥬", shelf_life_days=14, image="zucchini.jpg"),
    dict(plu=110, name="Часник", unit="weight", price=189.00, category="Овочі", emoji="🥬", shelf_life_days=90, image="garlic.jpg"),
    # --- Фрукти ---
    dict(plu=201, name="Яблука Голден", unit="weight", price=42.90, category="Фрукти", emoji="🍎", shelf_life_days=21, image="apple-golden.jpg"),
    dict(plu=202, name="Банани", unit="weight", price=48.70, category="Фрукти", emoji="🍎", shelf_life_days=7, image="banana.jpg"),
    dict(plu=203, name="Виноград Кишміш", unit="weight", price=139.00, category="Фрукти", emoji="🍎", shelf_life_days=10, image="grapes.jpg"),
    dict(plu=204, name="Мандарини", unit="weight", price=95.00, category="Фрукти", emoji="🍎", shelf_life_days=14, image="mandarin.jpg"),
    dict(plu=205, name="Груші Конференція", unit="weight", price=78.00, category="Фрукти", emoji="🍎", shelf_life_days=14, image="pear.jpg"),
    dict(plu=206, name="Апельсини", unit="weight", price=69.90, category="Фрукти", emoji="🍎", shelf_life_days=21, image="orange.jpg"),
    dict(plu=207, name="Лимони", unit="weight", price=89.00, category="Фрукти", emoji="🍎", shelf_life_days=30, image="lemon.jpg"),
    dict(plu=208, name="Ківі", unit="weight", price=112.00, category="Фрукти", emoji="🍎", shelf_life_days=21, image="kiwi.jpg"),
    dict(plu=209, name="Полуниця", unit="weight", price=249.00, category="Фрукти", emoji="🍎", shelf_life_days=3, image="strawberry.jpg"),
    dict(plu=210, name="Гранат", unit="weight", price=159.00, category="Фрукти", emoji="🍎", shelf_life_days=30, image="pomegranate.jpg"),
    # --- М'ясо ---
    dict(plu=301, name="Філе куряче", unit="weight", price=189.90, category="М'ясо", emoji="🥩", shelf_life_days=3, tare_g=12, image="chicken-fillet.jpg"),
    dict(plu=302, name="Фарш свинячий", unit="weight", price=229.00, category="М'ясо", emoji="🥩", shelf_life_days=2, tare_g=12, image="minced-pork.jpg"),
    dict(plu=303, name="Стейк яловичий", unit="weight", price=489.00, category="М'ясо", emoji="🥩", shelf_life_days=3, tare_g=12, image="beef-steak.jpg"),
    dict(plu=304, name="Крильця курячі", unit="weight", price=149.00, category="М'ясо", emoji="🥩", shelf_life_days=3, tare_g=12, image="chicken-wings.jpg"),
    # --- Сири ---
    dict(plu=401, name="Сир Гауда", unit="weight", price=449.00, category="Сири", emoji="🧀", shelf_life_days=30, image="cheese-gouda.jpg"),
    dict(plu=402, name="Сир Бринза", unit="weight", price=289.00, category="Сири", emoji="🧀", shelf_life_days=14, image="cheese-brynza.jpg"),
    dict(plu=403, name="Сир Пармезан", unit="weight", price=799.00, category="Сири", emoji="🧀", shelf_life_days=60, image="cheese-parmesan.jpg"),
    dict(plu=404, name="Сир Моцарела", unit="weight", price=359.00, category="Сири", emoji="🧀", shelf_life_days=14, image="cheese-mozzarella.jpg"),
    # --- Горіхи ---
    dict(plu=501, name="Горіх волоський", unit="weight", price=399.00, category="Горіхи", emoji="🌰", shelf_life_days=90, image="walnut.jpg"),
    dict(plu=502, name="Родзинки", unit="weight", price=169.00, category="Горіхи", emoji="🌰", shelf_life_days=180, image="raisins.jpg"),
    dict(plu=503, name="Мигдаль", unit="weight", price=549.00, category="Горіхи", emoji="🌰", shelf_life_days=180, image="almond.jpg"),
    dict(plu=504, name="Фундук", unit="weight", price=479.00, category="Горіхи", emoji="🌰", shelf_life_days=180, image="hazelnut.jpg"),
    # --- Випічка ---
    dict(plu=601, name="Батон нарізний", unit="piece", price=32.50, category="Випічка", emoji="🥖", shelf_life_days=2, image="bread-loaf.jpg"),
    dict(plu=602, name="Багет французький", unit="piece", price=45.00, category="Випічка", emoji="🥖", shelf_life_days=1, image="baguette.jpg"),
    dict(plu=603, name="Круасан", unit="piece", price=38.00, category="Випічка", emoji="🥖", shelf_life_days=2, image="croissant.jpg"),
    # --- Риба ---
    dict(plu=701, name="Філе лосося", unit="weight", price=689.00, category="Риба", emoji="🐟", shelf_life_days=2, tare_g=12, image="salmon.jpg"),
    dict(plu=702, name="Оселедець", unit="weight", price=139.00, category="Риба", emoji="🐟", shelf_life_days=5, tare_g=12, image="herring.jpg"),
    dict(plu=703, name="Креветки варені", unit="weight", price=549.00, category="Риба", emoji="🐟", shelf_life_days=3, image="shrimp.jpg"),
    # --- Молочне ---
    dict(plu=801, name="Масло вершкове", unit="weight", price=429.00, category="Молочне", emoji="🥛", shelf_life_days=20, image="butter.jpg"),
    dict(plu=802, name="Сметана 20%", unit="piece", price=62.00, category="Молочне", emoji="🥛", shelf_life_days=10, image="sour-cream.jpg"),
    dict(plu=803, name="Йогурт натуральний", unit="piece", price=38.50, category="Молочне", emoji="🥛", shelf_life_days=14, image="yogurt.jpg"),
    # --- Ковбаси ---
    dict(plu=901, name="Ковбаса варена", unit="weight", price=219.00, category="Ковбаси", emoji="🌭", shelf_life_days=7, tare_g=12, image="sausage.jpg"),
    dict(plu=902, name="Салямі", unit="weight", price=459.00, category="Ковбаси", emoji="🌭", shelf_life_days=30, tare_g=12, image="salami.jpg"),
    dict(plu=903, name="Шинка", unit="weight", price=329.00, category="Ковбаси", emoji="🌭", shelf_life_days=7, tare_g=12, image="ham.jpg"),
    # --- Крупи ---
    dict(plu=1001, name="Рис довгозернистий", unit="weight", price=62.00, category="Крупи", emoji="🌾", shelf_life_days=365, image="rice.jpg"),
    dict(plu=1002, name="Гречка", unit="weight", price=58.00, category="Крупи", emoji="🌾", shelf_life_days=365, image="buckwheat.jpg"),
    dict(plu=1003, name="Вівсяні пластівці", unit="weight", price=44.00, category="Крупи", emoji="🌾", shelf_life_days=180, image="oat-flakes.jpg"),
    dict(plu=1004, name="Макарони", unit="weight", price=49.00, category="Крупи", emoji="🌾", shelf_life_days=365, image="pasta.jpg"),
    # --- Солодощі ---
    dict(plu=1101, name="Цукерки шоколадні", unit="weight", price=389.00, category="Солодощі", emoji="🍬", shelf_life_days=180, image="chocolate.jpg"),
    dict(plu=1102, name="Печиво вівсяне", unit="weight", price=149.00, category="Солодощі", emoji="🍬", shelf_life_days=90, image="cookies.jpg"),
    dict(plu=1103, name="Мед квітковий", unit="piece", price=249.00, category="Солодощі", emoji="🍬", shelf_life_days=365, image="honey.jpg"),
    # --- Спеції ---
    dict(plu=1201, name="Перець чорний", unit="weight", price=899.00, category="Спеції", emoji="🧂", shelf_life_days=365, image="black-pepper.jpg"),
    dict(plu=1202, name="Паприка мелена", unit="weight", price=459.00, category="Спеції", emoji="🧂", shelf_life_days=365, image="paprika.jpg"),
    dict(plu=1203, name="Кориця", unit="weight", price=699.00, category="Спеції", emoji="🧂", shelf_life_days=365, image="cinnamon.jpg"),]


def seed_if_empty(db: Session) -> int:
    if db.scalar(select(Product).limit(1)) is not None:
        return 0
    db.add_all(Product(**item) for item in DEMO_PRODUCTS)
    db.commit()
    return len(DEMO_PRODUCTS)
