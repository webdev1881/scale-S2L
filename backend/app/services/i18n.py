"""Переводы для текстов, которые формирует бэкенд.

Сюда попадает только то, что фронтенд перевести не может: надписи, впечатанные в растр
этикетки. Ошибки устройств бэкенд отдаёт кодами (`errors.py`) — их переводит интерфейс,
потому что язык интерфейса может отличаться от языка печати.
"""
from __future__ import annotations

from typing import Final

DEFAULT_LANG: Final = "uk"
SUPPORTED_LANGS: Final = ("uk", "ru")

LABEL: Final[dict[str, dict[str, str]]] = {
    # Подписи короткие и с двоеточием: на этикетке они стоят в строку со
    # значением, как на образце торговой сети. Единица измерения в подпись не
    # входит — она и так ясна из самой этикетки, а место на ленте дорого.
    "uk": {
        "mass": "Вага:",
        "price_per_kg": "Ціна:",
        "quantity": "Кількість:",
        "price_per_piece": "Ціна:",
        "one_piece": "1 шт",
        "total": "Вартість:",
        "packed": "Дата пак.",
        "best_before": "Придатний до",
        "thanks": "Дякуємо за покупку! Приходьте ще!",
    },
    "ru": {
        "mass": "Вес:",
        "price_per_kg": "Цена:",
        "quantity": "Количество:",
        "price_per_piece": "Цена:",
        "one_piece": "1 шт",
        "total": "Стоимость:",
        "packed": "Дата упак.",
        "best_before": "Годен до",
        "thanks": "Спасибо за покупку! Приходите ещё!",
    },
}


def label_text(lang: str, key: str, **params: object) -> str:
    table = LABEL.get(lang) or LABEL[DEFAULT_LANG]
    template = table.get(key) or LABEL[DEFAULT_LANG].get(key, key)
    return template.format(**params) if params else template
