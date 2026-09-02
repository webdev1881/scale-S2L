from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    """Позиция каталога. plu — номер, который кассир/покупатель набирает на клавиатуре."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plu: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    # weight — цена за кг, piece — цена за штуку
    unit: Mapped[str] = mapped_column(String(10), default="weight")
    price: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(String(60), default="")
    tare_g: Mapped[int] = mapped_column(Integer, default=0)
    shelf_life_days: Mapped[int] = mapped_column(Integer, default=0)
    composition: Mapped[str] = mapped_column(Text, default="")
    emoji: Mapped[str] = mapped_column(String(8), default="")
    # Имя файла в frontend/public/products; пусто — карточка покажет значок
    image: Mapped[str] = mapped_column(String(120), default="")
    active: Mapped[int] = mapped_column(Integer, default=1)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="product")


class Transaction(Base):
    """Факт печати этикетки. Локальный журнал; на Фазе 4 выгружается в центр."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Время локальное, а не UTC: журнал должен совпадать с тем, что напечатано на этикетке.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(120))
    weight_g: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    barcode: Mapped[str] = mapped_column(String(20), default="")
    label_file: Mapped[str] = mapped_column(String(120), default="")

    product: Mapped[Product] = relationship(back_populates="transactions")

