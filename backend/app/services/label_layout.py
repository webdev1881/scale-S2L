"""Раскладка этикетки: что где напечатано.

Раньше порядок блоков был зашит в код рендера, и «подвинуть штрихкод» означало
правку исходников. Теперь раскладка — данные: список блоков с координатами в
миллиметрах, а рендер просто идёт по списку. Это и позволяет собрать конструктор
в админке, не заводя второй путь отрисовки: превью и печать по-прежнему делает
один и тот же `render_label`.

Координаты в миллиметрах, а не в точках: оператор меряет этикетку линейкой, а
разрешение печатающего узла (8 точек на миллиметр) — деталь железа.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Что умеет печатать блок. Значения берутся из данных чека, кроме `text` (своя
# надпись) и `line` (разделительная черта).
BlockKind = Literal[
    "store",
    "name",
    "weight",
    "price",
    "total",
    "barcode",
    "packed",
    "best_before",
    "composition",
    "text",
    "line",
]


class LabelBlock(BaseModel):
    kind: BlockKind
    # Левый верхний угол и размеры в миллиметрах. Нулевая ширина — «до правого
    # края этикетки»: так блок не приходится править после смены ширины ленты.
    x: float = Field(default=2, ge=0, le=200)
    y: float = Field(default=2, ge=0, le=200)
    width: float = Field(default=0, ge=0, le=200)
    height: float = Field(default=0, ge=0, le=200)
    # Кегль в точках растра: шрифт грузится по пикселям, и пересчёт в миллиметры
    # только запутал бы — на этикетке принято говорить о кегле.
    size: int = Field(default=20, ge=8, le=96)
    bold: bool = False
    align: Literal["left", "center", "right"] = "left"
    # Подпись над значением («Маса», «Ціна за кг») — берётся из словаря по языку.
    caption: bool = False
    # Сколько строк отдать длинному тексту: название и состав переносятся, хвост
    # обрезается многоточием.
    lines: int = Field(default=1, ge=1, le=6)
    # Рамка вокруг блока — ею выделяют сумму к оплате.
    box: bool = False
    text: str = ""
    visible: bool = True


def default_blocks() -> list[LabelBlock]:
    """Заводская раскладка — та же этикетка, что печаталась до конструктора."""
    return [
        LabelBlock(kind="store", x=1.5, y=1.5, size=18),
        LabelBlock(kind="line", x=1.5, y=4.5, height=0.2),
        LabelBlock(kind="name", x=1.5, y=5.2, size=26, bold=True, lines=2),
        LabelBlock(kind="weight", x=1.5, y=13, size=22, bold=True, caption=True),
        LabelBlock(kind="price", x=28, y=13, size=22, bold=True, caption=True),
        LabelBlock(kind="total", x=1.5, y=19.5, width=53, height=5.5, size=34, bold=True,
                   align="right", caption=True, box=True),
        LabelBlock(kind="packed", x=1.5, y=26, size=15),
        LabelBlock(kind="barcode", x=1.5, y=29.5, height=9, size=16),
    ]


class LabelLayout(BaseModel):
    blocks: list[LabelBlock] = Field(default_factory=default_blocks)
