"""Симулятор принтера: вместо бумаги — PNG-файл, который показывается в браузере."""
from __future__ import annotations

import asyncio
from datetime import datetime

from ...config import LABELS_DIR
from ...errors import PrintCode, PrintError
from ..base import DeviceStatus, PrinterDevice, PrintJob

# Сколько последних этикеток храним на диске
KEEP_LABELS = 200


class FakePrinter(PrinterDevice):
    def __init__(self) -> None:
        self._paper_out = False
        self._cover_open = False
        self._printed = 0

    # --- управление симуляцией ---
    def sim_paper_out(self, value: bool) -> None:
        self._paper_out = bool(value)

    def sim_cover_open(self, value: bool) -> None:
        self._cover_open = bool(value)

    # --- PrinterDevice ---
    async def start(self) -> None:
        LABELS_DIR.mkdir(parents=True, exist_ok=True)

    async def stop(self) -> None:
        return None

    async def print_label(self, job: PrintJob) -> str:
        if self._paper_out:
            raise PrintError(PrintCode.PAPER_OUT)
        if self._cover_open:
            raise PrintError(PrintCode.COVER_OPEN)
        await asyncio.sleep(0.4)  # реальная печать не мгновенна — UI должен это переживать
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        filename = f"{stamp}.png"
        (LABELS_DIR / filename).write_bytes(job.png_bytes)
        self._printed += 1
        self._cleanup()
        return filename

    def _cleanup(self) -> None:
        files = sorted(LABELS_DIR.glob("*.png"))
        for stale in files[:-KEEP_LABELS]:
            stale.unlink(missing_ok=True)

    def status(self) -> DeviceStatus:
        online = not self._paper_out and not self._cover_open
        return DeviceStatus(
            online=online,
            kind="fake",
            detail={
                "paper_out": self._paper_out,
                "cover_open": self._cover_open,
                "printed": self._printed,
            },
        )
