"""Драйвер весовой платы Aurora S2 (встроенный RS232).

Формат кадра подтверждён на приборе (issue #1): 8 байт, из них байты 1..6 —
ASCII-цифры массы в граммах, крайние байты обрамляющие. Пример: b"\\x02001240\\x03"
даёт 1240 г. Скорость 19200, 8N1, порт /dev/ttyS4.

Два решения, за которыми стоит опыт первой (неработавшей) версии:

1. Чтение идёт в отдельном потоке обычным блокирующим pyserial, а не через
   serial_asyncio. Асинхронная обёртка над последовательным портом добавляла
   слой, в котором ошибка и пряталась, а выигрыша не давала: поток здесь всё
   равно один и всё, что он делает, — ждёт байты.

2. Кадры выцепляются из потока по признаку «шесть цифр подряд между двумя
   нецифровыми байтами», а не отрезаются вслепую по 8 байт от начала чтения.
   Слепое чтение рассинхронизируется после любой потери байта и начинает
   склеивать половинки соседних кадров в правдоподобные, но неверные числа —
   на весах это означает неверную цену на этикетке.
"""
from __future__ import annotations

import threading
import time
from collections import deque

from ...errors import ScaleError
from ..base import DeviceStatus, ScaleDevice, WeightReading

FRAME_LEN = 8
DIGITS_FROM = 1
DIGITS_TO = 7  # байты 1..6 включительно

# Сколько одинаковых отсчётов подряд считаем устоявшимся весом. Плата признака
# стабильности не передаёт, поэтому определяем его на стороне ПК.
STABLE_SAMPLES = 5
# Молчание дольше этого времени считаем обрывом связи.
SILENCE_TIMEOUT_S = 2.0


class SerialScale(ScaleDevice):
    def __init__(self, port: str, baudrate: int = 19200, division_g: int = 5) -> None:
        self.port = port
        self.baudrate = baudrate
        self.division_g = max(1, division_g)

        self._serial = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._buffer = bytearray()
        self._history: deque[int] = deque(maxlen=STABLE_SAMPLES)

        self._gross_g = 0
        self._tare_g = 0
        self._stable = False
        self._error: str | None = ScaleError.NO_LINK
        self._error_detail = ""
        self._frames = 0
        self._last_frame_at = 0.0
        # Обрамляющие байты кадра фиксируем как есть: их назначение (STX/ETX, знак,
        # признак стабильности) выясняется на приборе, а не додумывается здесь.
        self._prefix = ""
        self._suffix = ""

    # --- ScaleDevice ---

    async def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="s2l-scale", daemon=True)
        self._thread.start()

    async def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=2.0)
        self._close()

    def read(self) -> WeightReading:
        return WeightReading(
            gross_g=self._gross_g,
            tare_g=self._tare_g,
            stable=self._stable,
            error=self._error,
        )

    async def tare(self) -> None:
        # Тару считаем на стороне ПК: поведение одинаково для fake и real.
        self._tare_g = self._gross_g

    async def zero(self) -> None:
        self._tare_g = 0

    def status(self) -> DeviceStatus:
        return DeviceStatus(
            online=self._error is None,
            kind="real",
            detail={
                "port": self.port,
                "baudrate": self.baudrate,
                "division_g": self.division_g,
                "frames": self._frames,
                "error": self._error,
                "error_detail": self._error_detail,
                "frame_prefix": self._prefix,
                "frame_suffix": self._suffix,
            },
        )

    # --- чтение порта ---

    def _loop(self) -> None:
        import serial  # локальный импорт: на dev-машине порта нет, а пакет может отсутствовать

        while not self._stop.is_set():
            try:
                if self._serial is None:
                    self._serial = serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=0.2,
                    )
                    self._buffer.clear()
                    self._last_frame_at = time.monotonic()

                chunk = self._serial.read(64)
                if chunk:
                    self._buffer.extend(chunk)
                    self._consume()
                elif time.monotonic() - self._last_frame_at > SILENCE_TIMEOUT_S:
                    self._fail("порт открыт, но кадры не приходят")
            except Exception as exc:  # обрыв кабеля, снятое питание платы, занятый порт
                self._fail(f"{type(exc).__name__}: {exc}")
                self._close()
                self._stop.wait(1.0)

    def _consume(self) -> None:
        """Выбирает кадры из потока, восстанавливая синхронизацию после сбоя."""
        buffer = self._buffer
        while len(buffer) >= FRAME_LEN:
            grams = self._parse_frame(buffer)
            if grams is None:
                del buffer[:1]  # сдвигаемся на байт и пробуем снова
                continue
            self._prefix = repr(bytes(buffer[:1]))
            self._suffix = repr(bytes(buffer[FRAME_LEN - 1 : FRAME_LEN]))
            del buffer[:FRAME_LEN]
            self._accept(grams)

        # Мусор без единого кадра не должен расти бесконечно.
        if len(buffer) > 4 * FRAME_LEN:
            del buffer[: len(buffer) - FRAME_LEN]

    @staticmethod
    def _parse_frame(buffer: bytearray) -> int | None:
        """Кадр = нецифровой байт, шесть цифр, нецифровой байт. Иначе не кадр."""
        head = buffer[0]
        tail = buffer[FRAME_LEN - 1]
        if 0x30 <= head <= 0x39 or 0x30 <= tail <= 0x39:
            return None
        digits = buffer[DIGITS_FROM:DIGITS_TO]
        if not all(0x30 <= byte <= 0x39 for byte in digits):
            return None
        grams = int(digits.decode("ascii"))
        # Знак минус в обрамлении: тара больше нетто на платформе.
        return -grams if head == 0x2D else grams

    def _accept(self, grams: int) -> None:
        self._gross_g = grams
        self._frames += 1
        self._last_frame_at = time.monotonic()
        self._error = None
        self._error_detail = ""

        self._history.append(grams)
        self._stable = (
            len(self._history) == self._history.maxlen
            and max(self._history) - min(self._history) <= self.division_g
        )

    def _fail(self, detail: str) -> None:
        self._error = ScaleError.NO_LINK
        self._error_detail = detail
        self._stable = False
        self._history.clear()

    def _close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
