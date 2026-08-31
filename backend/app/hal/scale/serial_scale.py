"""Драйвер реальной весовой платы (последовательный порт).

ВНИМАНИЕ: конкретный кадр протокола Aurora S2L подтверждается на Фазе 0 (перехват
обмена штатного ПО). Здесь реализован разбор распространённого ASCII-формата
Toledo/Rongta вида:

    ST,GS,+  1.234kg\r\n
    US,GS,+  0.512kg\r\n

ST — устоявшийся вес, US — нестабильный. Если у платы окажется бинарный кадр,
меняется только _parse_frame(); остальной код и весь UI не затрагиваются.
"""
from __future__ import annotations

import asyncio
import re

from ...errors import ScaleError
from ..base import DeviceStatus, ScaleDevice, WeightReading

FRAME_RE = re.compile(
    rb"(?P<stab>ST|US)\s*,\s*(?:GS|NT)\s*,\s*(?P<sign>[+-])\s*(?P<value>[\d.]+)\s*(?P<unit>kg|g)",
    re.IGNORECASE,
)


class SerialScale(ScaleDevice):
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._task: asyncio.Task | None = None
        self._last = WeightReading(gross_g=0, tare_g=0, stable=False, error=ScaleError.NO_LINK)
        self._tare_g = 0
        self._connected = False
        self._error_detail = ""

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        if self._writer is not None:
            self._writer.close()
            self._writer = None

    async def _connect(self) -> None:
        import serial_asyncio  # импорт локальный: на dev-машине пакет может отсутствовать

        self._reader, self._writer = await serial_asyncio.open_serial_connection(
            url=self.port, baudrate=self.baudrate
        )
        self._connected = True

    async def _loop(self) -> None:
        while True:
            try:
                if not self._connected:
                    await self._connect()
                assert self._reader is not None
                line = await asyncio.wait_for(self._reader.readline(), timeout=2.0)
                if not line:
                    raise ConnectionError("порт закрыт")
                parsed = self._parse_frame(line)
                if parsed is not None:
                    self._last = parsed
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # обрыв USB, снятое питание платы, мусор в порту
                self._connected = False
                self._error_detail = str(exc)
                self._last = WeightReading(
                    gross_g=0, tare_g=self._tare_g, stable=False, error=ScaleError.NO_LINK
                )
                await asyncio.sleep(1.0)

    def _parse_frame(self, raw: bytes) -> WeightReading | None:
        m = FRAME_RE.search(raw)
        if m is None:
            return None
        value = float(m.group("value").decode())
        if m.group("unit").lower() == b"kg":
            value *= 1000
        if m.group("sign") == b"-":
            value = -value
        return WeightReading(
            gross_g=int(round(value)),
            tare_g=self._tare_g,
            stable=m.group("stab").upper() == b"ST",
        )

    def read(self) -> WeightReading:
        return WeightReading(
            gross_g=self._last.gross_g,
            tare_g=self._tare_g,
            stable=self._last.stable,
            error=self._last.error,
        )

    async def tare(self) -> None:
        # Тару считаем на стороне ПК: так поведение одинаково для fake и real.
        # Если плата умеет аппаратную тару — здесь шлём её команду (уточняется на Фазе 0).
        self._tare_g = self._last.gross_g

    async def zero(self) -> None:
        self._tare_g = 0

    def status(self) -> DeviceStatus:
        return DeviceStatus(
            online=self._connected,
            kind="real",
            detail={
                "port": self.port,
                "baudrate": self.baudrate,
                "error": self._last.error,
                "error_detail": self._error_detail,
            },
        )
