"""Драйвер реального принтера: прямая запись TSPL в символьное устройство.

CUPS сознательно не используется — лишний слой, задержка и очередь, которая на киоске
только мешает. Доступ к /dev/usb/lp0 выдаётся udev-правилом (см. deploy/udev/).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from ..base import DeviceStatus, PrinterDevice, PrintJob


class UsbRawPrinter(PrinterDevice):
    def __init__(self, device: str) -> None:
        self.device = Path(device)
        self._lock = asyncio.Lock()
        self._printed = 0
        self._last_error: str | None = None

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def print_label(self, job: PrintJob) -> str:
        # Один воркер на устройство: параллельная запись в lp0 перемешает задания.
        async with self._lock:
            try:
                await asyncio.to_thread(self._write, job.tspl)
                self._printed += 1
                self._last_error = None
            except OSError as exc:
                self._last_error = str(exc)
                raise RuntimeError(f"Принтер недоступен: {exc}") from exc
        return ""

    def _write(self, payload: bytes) -> None:
        with self.device.open("wb", buffering=0) as fh:
            fh.write(payload)

    def status(self) -> DeviceStatus:
        exists = self.device.exists()
        return DeviceStatus(
            online=exists and self._last_error is None,
            kind="real",
            detail={
                "device": str(self.device),
                "exists": exists,
                "printed": self._printed,
                "error": self._last_error,
            },
        )
