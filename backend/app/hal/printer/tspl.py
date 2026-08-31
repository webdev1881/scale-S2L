"""Сборка команд TSPL/TSPL2 для принтера этикеток.

Текст рисуется не встроенными шрифтами принтера, а растром: встроенные шрифты Rongta
обычно не содержат кириллицы, а растр даёт полный контроль над начертанием.
Штрихкод тоже уходит растром — так превью в браузере гарантированно совпадает с бумагой.
"""
from __future__ import annotations

from PIL import Image


def image_to_bitmap_payload(img: Image.Image) -> tuple[int, int, bytes]:
    """PIL-изображение -> (ширина в байтах, высота, данные) для команды BITMAP.

    В TSPL бит 0 — чёрная точка, бит 1 — белая, поэтому изображение инвертируется.
    """
    mono = img.convert("1")
    width, height = mono.size
    width_bytes = (width + 7) // 8
    pixels = mono.load()
    out = bytearray()
    for y in range(height):
        for bx in range(width_bytes):
            byte = 0
            for bit in range(8):
                x = bx * 8 + bit
                white = 1 if (x >= width or pixels[x, y] != 0) else 0
                byte = (byte << 1) | white
            out.append(byte)
    return width_bytes, height, bytes(out)


def build_label_tspl(
    img: Image.Image,
    width_mm: float,
    height_mm: float,
    gap_mm: float = 2.0,
    copies: int = 1,
    density: int = 8,
    speed: int = 4,
) -> bytes:
    width_bytes, height, payload = image_to_bitmap_payload(img)
    header = (
        f"SIZE {width_mm:g} mm,{height_mm:g} mm\r\n"
        f"GAP {gap_mm:g} mm,0 mm\r\n"
        f"DENSITY {density}\r\n"
        f"SPEED {speed}\r\n"
        "DIRECTION 1\r\n"
        "CLS\r\n"
        f"BITMAP 0,0,{width_bytes},{height},0,"
    ).encode("ascii")
    footer = f"\r\nPRINT {copies},1\r\n".encode("ascii")
    return header + payload + footer
