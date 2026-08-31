"""Коды состояний железа и отказов печати.

Бэкенд возвращает код, интерфейс подбирает формулировку на своём языке. Так текст
не приходится дублировать в двух местах и переводить строку обратно в смысл.
"""
from __future__ import annotations


class ScaleError:
    NO_LINK = "scale.no_link"
    OVERLOAD = "scale.overload"


class PrintError(RuntimeError):
    """Печать невозможна. `code` — машинный признак, `detail` — техника для логов."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


class PrintCode:
    PAPER_OUT = "print.paper_out"
    COVER_OPEN = "print.cover_open"
    UNAVAILABLE = "print.unavailable"
    NOT_STABLE = "print.not_stable"
    NO_GOODS = "print.no_goods"
    SCALE_ERROR = "print.scale_error"
