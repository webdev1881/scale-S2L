"""Рендер этикетки: данные -> растр -> команды принтера.

Растр один и тот же и для превью в браузере, и для печати, поэтому «на экране одно,
на бумаге другое» здесь структурно невозможно.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime

from PIL import Image, ImageDraw

from ..hal.base import PrintJob
from ..hal.printer.tspl import build_label_tspl
from .barcode import ean13_pattern
from .fonts import load_font

DOTS_PER_MM = 8  # 203 dpi — стандарт термопринтеров этикеток


@dataclass
class LabelData:
    store_name: str
    product_name: str
    weight_g: int
    price: float
    total: float
    unit: str  # weight | piece
    currency: str
    barcode: str
    packed_at: datetime
    best_before: datetime | None
    composition: str = ""


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Перенос по словам, максимум две строки; хвост обрезается многоточием."""
    words, lines, current = text.split(), [], ""
    for word in words:
        probe = f"{current} {word}".strip()
        if draw.textlength(probe, font=font) <= max_width or not current:
            current = probe
        else:
            lines.append(current)
            current = word
            if len(lines) == 2:
                break
    if current and len(lines) < 2:
        lines.append(current)
    if len(lines) == 2 and draw.textlength(lines[1], font=font) > max_width:
        while lines[1] and draw.textlength(lines[1] + "…", font=font) > max_width:
            lines[1] = lines[1][:-1]
        lines[1] += "…"
    return lines


def render_label(data: LabelData, width_mm: float = 60, height_mm: float = 40) -> Image.Image:
    width = int(width_mm * DOTS_PER_MM)
    height = int(height_mm * DOTS_PER_MM)
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    pad = 10
    f_shop = load_font(18)
    f_name = load_font(26, bold=True)
    f_key = load_font(17)
    f_val = load_font(22, bold=True)
    f_total = load_font(34, bold=True)
    f_small = load_font(15)

    y = pad
    draw.text((pad, y), data.store_name[:40], font=f_shop, fill=0)
    y += 22
    draw.line((pad, y, width - pad, y), fill=0, width=1)
    y += 6

    for line in _fit_text(draw, data.product_name, f_name, width - 2 * pad):
        draw.text((pad, y), line, font=f_name, fill=0)
        y += 30

    y += 2
    col2 = width // 2
    if data.unit == "weight":
        draw.text((pad, y), "Масса, кг", font=f_key, fill=0)
        draw.text((col2, y), "Цена, {}/кг".format(data.currency), font=f_key, fill=0)
        y += 19
        draw.text((pad, y), f"{data.weight_g / 1000:.3f}", font=f_val, fill=0)
        draw.text((col2, y), f"{data.price:.2f}", font=f_val, fill=0)
    else:
        draw.text((pad, y), "Количество", font=f_key, fill=0)
        draw.text((col2, y), "Цена, {}/шт".format(data.currency), font=f_key, fill=0)
        y += 19
        draw.text((pad, y), "1 шт", font=f_val, fill=0)
        draw.text((col2, y), f"{data.price:.2f}", font=f_val, fill=0)
    y += 30

    draw.rectangle((pad, y, width - pad, y + 44), outline=0, width=2)
    draw.text((pad + 8, y + 10), "К оплате", font=f_key, fill=0)
    total_text = f"{data.total:.2f} {data.currency}"
    draw.text(
        (width - pad - 8 - draw.textlength(total_text, font=f_total), y + 5),
        total_text,
        font=f_total,
        fill=0,
    )
    y += 52

    stamp = f"Упаковано: {data.packed_at:%d.%m.%Y %H:%M}"
    if data.best_before:
        stamp += f"   Годен до: {data.best_before:%d.%m.%Y}"
    draw.text((pad, y), stamp, font=f_small, fill=0)
    y += 18

    _draw_barcode(draw, data.barcode, x=pad, y=y, width=width - 2 * pad, height=height - y - pad)
    return img


def _draw_barcode(draw: ImageDraw.ImageDraw, code: str, x: int, y: int, width: int, height: int) -> None:
    try:
        pattern = ean13_pattern(code)
    except ValueError:
        draw.text((x, y), code, font=load_font(16), fill=0)
        return
    f_digits = load_font(16)
    bars_height = max(height - 18, 20)
    module = max(width // len(pattern), 1)
    bar_x = x + (width - module * len(pattern)) // 2
    for i, bit in enumerate(pattern):
        if bit == "1":
            draw.rectangle(
                (bar_x + i * module, y, bar_x + (i + 1) * module - 1, y + bars_height), fill=0
            )
    text_width = draw.textlength(code, font=f_digits)
    draw.text((x + (width - text_width) / 2, y + bars_height + 1), code, font=f_digits, fill=0)


def build_print_job(data: LabelData, width_mm: float, height_mm: float, copies: int = 1) -> PrintJob:
    img = render_label(data, width_mm, height_mm)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return PrintJob(
        name=data.product_name,
        width_px=img.width,
        height_px=img.height,
        png_bytes=buf.getvalue(),
        tspl=build_label_tspl(img, width_mm, height_mm, copies=copies),
    )
