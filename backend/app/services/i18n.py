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
    "uk": {
        "mass": "Маса, кг",
        "price_per_kg": "Ціна, {currency}/кг",
        "quantity": "Кількість",
        "price_per_piece": "Ціна, {currency}/шт",
        "one_piece": "1 шт",
        "total": "До сплати",
        "packed": "Упаковано",
        "best_before": "Придатний до",
    },
    "ru": {
        "mass": "Масса, кг",
        "price_per_kg": "Цена, {currency}/кг",
        "quantity": "Количество",
        "price_per_piece": "Цена, {currency}/шт",
        "one_piece": "1 шт",
        "total": "К оплате",
        "packed": "Упаковано",
        "best_before": "Годен до",
    },
}


def label_text(lang: str, key: str, **params: object) -> str:
    table = LABEL.get(lang) or LABEL[DEFAULT_LANG]
    template = table.get(key) or LABEL[DEFAULT_LANG].get(key, key)
    return template.format(**params) if params else template
