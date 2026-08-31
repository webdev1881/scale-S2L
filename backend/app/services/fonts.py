"""Поиск TTF со славянской кириллицей. На киоске ставится fonts-dejavu-core."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
]
BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]


def _first_existing(candidates: list[str]) -> str | None:
    for path in candidates:
        if Path(path).exists():
            return path
    return None


@lru_cache(maxsize=64)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _first_existing(BOLD_CANDIDATES if bold else REGULAR_CANDIDATES)
    if path is None:
        # Крайний случай: встроенный растровый шрифт без кириллицы.
        return ImageFont.load_default()
    return ImageFont.truetype(path, size)
