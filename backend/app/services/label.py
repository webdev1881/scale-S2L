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
from .i18n import DEFAULT_LANG, label_text
from .label_layout import LabelBlock, LabelLayout

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
    lang: str = DEFAULT_LANG


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int = 2) -> list[str]:
    """Перенос по словам; хвост последней разрешённой строки обрезается многоточием."""
    words, lines, current = text.split(), [], ""
    for word in words:
        probe = f"{current} {word}".strip()
        if draw.textlength(probe, font=font) <= max_width or not current:
            current = probe
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    last = len(lines) - 1
    if lines and draw.textlength(lines[last], font=font) > max_width:
        while lines[last] and draw.textlength(lines[last] + "…", font=font) > max_width:
            lines[last] = lines[last][:-1]
        lines[last] += "…"
    return lines


def _block_value(data: "LabelData", block: LabelBlock) -> tuple[str, str]:
    """Подпись и значение блока. Пустая строка означает «печатать нечего»."""
    lang = data.lang
    if block.kind == "store":
        return "", data.store_name[:40]
    if block.kind == "name":
        return "", data.product_name
    if block.kind == "weight":
        if data.unit == "weight":
            return label_text(lang, "mass"), f"{data.weight_g / 1000:.3f}"
        return label_text(lang, "quantity"), label_text(lang, "one_piece")
    if block.kind == "price":
        key = "price_per_kg" if data.unit == "weight" else "price_per_piece"
        return label_text(lang, key, currency=data.currency), f"{data.price:.2f}"
    if block.kind == "total":
        return label_text(lang, "total"), f"{data.total:.2f} {data.currency}"
    if block.kind == "packed":
        return "", f"{label_text(lang, 'packed')}: {data.packed_at:%d.%m.%Y %H:%M}"
    if block.kind == "best_before":
        if not data.best_before:
            return "", ""
        return "", f"{label_text(lang, 'best_before')}: {data.best_before:%d.%m.%Y}"
    if block.kind == "composition":
        return "", data.composition
    if block.kind == "text":
        return "", block.text
    return "", ""


def _draw_block(
    draw: ImageDraw.ImageDraw, data: "LabelData", block: LabelBlock, width: int, height: int
) -> None:
    if not block.visible:
        return
    x = int(block.x * DOTS_PER_MM)
    y = int(block.y * DOTS_PER_MM)
    pad = int(1.5 * DOTS_PER_MM)
    # Нулевая ширина — до правого края: так блок переживает смену ширины ленты.
    box_width = int(block.width * DOTS_PER_MM) if block.width else max(width - x - pad, 1)
    box_height = int(block.height * DOTS_PER_MM)

    if block.kind == "line":
        draw.line((x, y, x + box_width, y), fill=0, width=max(box_height, 1))
        return

    if block.kind == "barcode":
        _draw_barcode(draw, data.barcode, x=x, y=y, width=box_width,
                      height=box_height or max(height - y - pad, 20), size=block.size)
        return

    caption, value = _block_value(data, block)
    if not value:
        return

    if block.box:
        draw.rectangle((x, y, x + box_width, y + max(box_height, block.size)), outline=0, width=2)

    inner = 8 if block.box else 0
    text_x = x + inner
    text_y = y + (4 if block.box else 0)
    text_width = box_width - 2 * inner

    if block.caption and caption:
        cap_font = load_font(max(block.size - 5, 10))
        draw.text((text_x, text_y), caption, font=cap_font, fill=0)
        # Значение уходит под подпись, если блок не в рамке: в рамке они стоят рядом.
        if not block.box:
            text_y += int(block.size * 0.8)

    font = load_font(block.size, bold=block.bold)
    lines = _fit_text(draw, value, font, text_width, block.lines)
    for line in lines:
        offset = 0.0
        if block.align != "left":
            free = text_width - draw.textlength(line, font=font)
            offset = free if block.align == "right" else free / 2
        draw.text((text_x + offset, text_y), line, font=font, fill=0)
        text_y += int(block.size * 1.15)


def render_label(
    data: LabelData,
    width_mm: float = 60,
    height_mm: float = 40,
    layout: LabelLayout | None = None,
) -> Image.Image:
    width = int(width_mm * DOTS_PER_MM)
    height = int(height_mm * DOTS_PER_MM)
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    for block in (layout or LabelLayout()).blocks:
        _draw_block(draw, data, block, width, height)
    return img


def _legacy_render(data: LabelData, width_mm: float, height_mm: float) -> Image.Image:
    """Прежняя жёсткая раскладка — оставлена как образец заводской."""
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
    lang = data.lang
    if data.unit == "weight":
        draw.text((pad, y), label_text(lang, "mass"), font=f_key, fill=0)
        draw.text(
            (col2, y), label_text(lang, "price_per_kg", currency=data.currency), font=f_key, fill=0
        )
        y += 19
        draw.text((pad, y), f"{data.weight_g / 1000:.3f}", font=f_val, fill=0)
        draw.text((col2, y), f"{data.price:.2f}", font=f_val, fill=0)
    else:
        draw.text((pad, y), label_text(lang, "quantity"), font=f_key, fill=0)
        draw.text(
            (col2, y),
            label_text(lang, "price_per_piece", currency=data.currency),
            font=f_key,
            fill=0,
        )
        y += 19
        draw.text((pad, y), label_text(lang, "one_piece"), font=f_val, fill=0)
        draw.text((col2, y), f"{data.price:.2f}", font=f_val, fill=0)
    y += 30

    draw.rectangle((pad, y, width - pad, y + 44), outline=0, width=2)
    draw.text((pad + 8, y + 10), label_text(lang, "total"), font=f_key, fill=0)
    total_text = f"{data.total:.2f} {data.currency}"
    draw.text(
        (width - pad - 8 - draw.textlength(total_text, font=f_total), y + 5),
        total_text,
        font=f_total,
        fill=0,
    )
    y += 52

    stamp = f"{label_text(lang, 'packed')}: {data.packed_at:%d.%m.%Y %H:%M}"
    if data.best_before:
        stamp += f"   {label_text(lang, 'best_before')}: {data.best_before:%d.%m.%Y}"
    draw.text((pad, y), stamp, font=f_small, fill=0)
    y += 18

    _draw_barcode(draw, data.barcode, x=pad, y=y, width=width - 2 * pad, height=height - y - pad)
    return img


def _draw_barcode(
    draw: ImageDraw.ImageDraw, code: str, x: int, y: int, width: int, height: int, size: int = 16
) -> None:
    try:
        pattern = ean13_pattern(code)
    except ValueError:
        draw.text((x, y), code, font=load_font(size), fill=0)
        return
    f_digits = load_font(size)
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


def build_print_job(
    data: LabelData,
    width_mm: float,
    height_mm: float,
    copies: int = 1,
    layout: LabelLayout | None = None,
) -> PrintJob:
    img = render_label(data, width_mm, height_mm, layout)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return PrintJob(
        name=data.product_name,
        width_px=img.width,
        height_px=img.height,
        png_bytes=buf.getvalue(),
        tspl=build_label_tspl(img, width_mm, height_mm, copies=copies),
    )
