"""Весы, принтер и симулятор железа."""
from __future__ import annotations

import asyncio
import io

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..config import get_settings
from ..errors import PrintError
from ..db import get_db
from ..hal.printer.fake import FakePrinter
from ..hal.registry import Devices, get_devices
from ..hal.scale.fake import FakeScale
from ..models import Product
from ..schemas import (
    DeviceStatusOut,
    LabelPreviewRequest,
    PrintRequest,
    PrintResult,
    SimPrinterIn,
    SimWeightIn,
    StatusOut,
    WeightOut,
)
from ..services.label import LabelData, render_label
from ..services.printing import build_barcode, compute_total, weigh_and_print
from ..services.settings_store import load_settings

router = APIRouter(prefix="/api", tags=["device"])


def _reading_out(devices: Devices) -> WeightOut:
    r = devices.scale.read()
    return WeightOut(
        gross_g=r.gross_g, net_g=r.net_g, tare_g=r.tare_g, stable=r.stable, error=r.error
    )


@router.get("/scale/weight", response_model=WeightOut)
def read_weight(devices: Devices = Depends(get_devices)) -> WeightOut:
    return _reading_out(devices)


@router.post("/scale/tare", response_model=WeightOut)
async def tare(devices: Devices = Depends(get_devices)) -> WeightOut:
    await devices.scale.tare()
    return _reading_out(devices)


@router.post("/scale/zero", response_model=WeightOut)
async def zero(devices: Devices = Depends(get_devices)) -> WeightOut:
    await devices.scale.zero()
    return _reading_out(devices)


@router.get("/status", response_model=StatusOut)
def device_status(devices: Devices = Depends(get_devices)) -> StatusOut:
    scale, printer = devices.scale.status(), devices.printer.status()
    return StatusOut(
        backend=devices.backend,
        scale=DeviceStatusOut(online=scale.online, kind=scale.kind, detail=scale.detail),
        printer=DeviceStatusOut(online=printer.online, kind=printer.kind, detail=printer.detail),
    )


@router.post("/print", response_model=PrintResult)
async def print_label(
    payload: PrintRequest,
    db: Session = Depends(get_db),
    devices: Devices = Depends(get_devices),
) -> PrintResult:
    product = db.get(Product, payload.product_id)
    if product is None or not product.active:
        raise HTTPException(404, "Товар не найден")
    settings = load_settings()
    try:
        tx = await weigh_and_print(
            db, devices, settings, product, payload.weight_g, payload.copies
        )
    except PrintError as exc:
        # 409, а не 500: это ожидаемый отказ. В detail уходит код — киоск сам подберёт
        # формулировку на своём языке.
        raise HTTPException(409, exc.code) from exc
    return PrintResult(
        transaction_id=tx.id,
        barcode=tx.barcode,
        weight_g=tx.weight_g,
        total=tx.total,
        label_url=f"/labels/{tx.label_file}" if tx.label_file else None,
    )


@router.post("/label/preview")
def label_preview(
    payload: LabelPreviewRequest,
    db: Session = Depends(get_db),
) -> Response:
    """PNG этикетки без печати — для админки и предпросмотра в киоске."""
    from datetime import datetime, timedelta

    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(404, "Товар не найден")
    settings = load_settings()
    total = compute_total(product, payload.weight_g)
    now = datetime.now()
    data = LabelData(
        store_name=settings.store_name,
        product_name=product.name,
        weight_g=payload.weight_g,
        price=product.price,
        total=total,
        unit=product.unit,
        currency=settings.currency,
        barcode=build_barcode(settings, product, payload.weight_g, total),
        packed_at=now,
        best_before=(now + timedelta(days=product.shelf_life_days))
        if product.shelf_life_days
        else None,
        composition=product.composition,
        lang=settings.language,
    )
    img = render_label(data, settings.label_width_mm, settings.label_height_mm)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png")


# --- Симулятор: доступен только при HAL_BACKEND=fake ---


@router.post("/sim/weight", response_model=WeightOut)
def sim_weight(payload: SimWeightIn, devices: Devices = Depends(get_devices)) -> WeightOut:
    if not isinstance(devices.scale, FakeScale):
        raise HTTPException(400, "Симулятор доступен только при HAL_BACKEND=fake")
    devices.scale.sim_put(payload.grams)
    return _reading_out(devices)


@router.post("/sim/printer")
def sim_printer(payload: SimPrinterIn, devices: Devices = Depends(get_devices)) -> dict:
    if not isinstance(devices.printer, FakePrinter):
        raise HTTPException(400, "Симулятор доступен только при HAL_BACKEND=fake")
    if payload.paper_out is not None:
        devices.printer.sim_paper_out(payload.paper_out)
    if payload.cover_open is not None:
        devices.printer.sim_cover_open(payload.cover_open)
    return devices.printer.status().detail


@router.websocket("/ws/weight")
async def ws_weight(websocket: WebSocket) -> None:
    """Поток веса. Киоск не опрашивает REST — он подписан на этот сокет."""
    await websocket.accept()
    devices = get_devices()
    period = 1.0 / get_settings().weight_stream_hz
    try:
        while True:
            r = devices.scale.read()
            await websocket.send_json(
                {
                    "gross_g": r.gross_g,
                    "net_g": r.net_g,
                    "tare_g": r.tare_g,
                    "stable": r.stable,
                    "error": r.error,
                }
            )
            await asyncio.sleep(period)
    except WebSocketDisconnect:
        return
