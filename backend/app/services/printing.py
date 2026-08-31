"""Сценарий «взвесить и напечатать» целиком: проверки -> расчёт -> печать -> журнал."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..errors import PrintCode, PrintError
from ..hal.registry import Devices
from ..models import Product, Transaction
from .barcode import build_weight_barcode
from .label import LabelData, build_print_job
from .settings_store import DeviceSettings


def compute_total(product: Product, weight_g: int) -> float:
    if product.unit == "piece":
        return round(product.price, 2)
    return round(product.price * weight_g / 1000, 2)


def build_barcode(settings: DeviceSettings, product: Product, weight_g: int, total: float) -> str:
    # У штучного товара масса бессмысленна, поэтому в штрихкод всегда уходит сумма.
    if product.unit == "piece" or settings.barcode_value == "total":
        value = int(round(total * 100))
    else:
        value = weight_g
    return build_weight_barcode(settings.barcode_template, product.plu, value)


async def weigh_and_print(
    db: Session,
    devices: Devices,
    settings: DeviceSettings,
    product: Product,
    weight_g: int | None,
    copies: int = 1,
) -> Transaction:
    reading = devices.scale.read()
    if product.unit == "piece":
        # Штучный товар не взвешивается: что бы ни лежало на платформе, масса в чек не идёт.
        weight_g = 0
    elif weight_g is None:
        weight_g = max(reading.net_g - product.tare_g, 0)

    if product.unit == "weight":
        if reading.error:
            raise PrintError(PrintCode.SCALE_ERROR, reading.error)
        if settings.require_stable and not reading.stable and weight_g == reading.net_g:
            raise PrintError(PrintCode.NOT_STABLE)
        if weight_g < settings.min_print_weight_g:
            raise PrintError(PrintCode.NO_GOODS)

    total = compute_total(product, weight_g)
    barcode = build_barcode(settings, product, weight_g, total)
    now = datetime.now()
    data = LabelData(
        store_name=settings.store_name,
        product_name=product.name,
        weight_g=weight_g,
        price=product.price,
        total=total,
        unit=product.unit,
        currency=settings.currency,
        barcode=barcode,
        packed_at=now,
        best_before=(now + timedelta(days=product.shelf_life_days))
        if product.shelf_life_days
        else None,
        composition=product.composition,
        lang=settings.language,
    )
    job = build_print_job(data, settings.label_width_mm, settings.label_height_mm, copies)

    label_file = await devices.printer.print_label(job)

    transaction = Transaction(
        product_id=product.id,
        product_name=product.name,
        weight_g=weight_g,
        price=product.price,
        total=total,
        barcode=barcode,
        label_file=label_file,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
