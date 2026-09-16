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
    "thanks",
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
    # Подпись рядом со значением («Вага:», «Ціна:») — берётся из словаря по языку.
    caption: bool = False
    # Подпись в той же строке, что и значение: подпись прижата влево, значение —
    # по `align`. Так свёрстан образец торговой сети, и так строка занимает вдвое
    # меньше высоты, чем подпись отдельной строкой сверху.
    caption_inline: bool = False
    # Сколько строк отдать длинному тексту: название и состав переносятся, хвост
    # обрезается многоточием.
    lines: int = Field(default=1, ge=1, le=6)
    # Рамка вокруг блока — ею выделяют сумму к оплате.
    box: bool = False
    text: str = ""
    visible: bool = True


def default_blocks() -> list[LabelBlock]:
    """Заводская раскладка — по образцу этикетки торговой сети.

    Сверху название в две строки, слева штрихкод, справа столбцом «Вага», «Ціна»
    и крупнее «Вартість», ниже название магазина и дата упаковки, внизу — строка
    благодарности во всю ширину. Размеры под ленту 56x40 мм.
    """
    return [
        LabelBlock(kind="name", x=1.5, y=0.8, size=24, bold=True, lines=2),
        LabelBlock(kind="barcode", x=1.5, y=9.5, width=26, height=10.5, size=15),
        LabelBlock(kind="weight", x=28.5, y=10, width=26, size=19, bold=True,
                   align="right", caption=True, caption_inline=True),
        LabelBlock(kind="price", x=28.5, y=14.6, width=26, size=19, bold=True,
                   align="right", caption=True, caption_inline=True),
        LabelBlock(kind="total", x=20, y=20.5, width=34.5, size=23, bold=True,
                   align="right", caption=True, caption_inline=True),
        LabelBlock(kind="store", x=1.5, y=25, size=30, bold=True),
        LabelBlock(kind="packed", x=25, y=30.5, width=29.5, size=14,
                   align="right", caption=True, caption_inline=True),
        LabelBlock(kind="thanks", x=1.5, y=34.8, size=16, bold=True, align="center"),
    ]


class LabelLayout(BaseModel):
    blocks: list[LabelBlock] = Field(default_factory=default_blocks)
