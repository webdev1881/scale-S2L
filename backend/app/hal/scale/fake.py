"""Симулятор весовой платы.

Имитирует то, что портит жизнь в реальности: инерцию нагрузки, шум АЦП и задержку
стабилизации. UI обязан корректно вести себя с «дрожащим» весом ещё до встречи с железом.
"""
from __future__ import annotations

import asyncio
import random

from ...errors import ScaleError
from ..base import DeviceStatus, ScaleDevice, WeightReading

# Порог, внутри которого вес считается неподвижным, и число подряд идущих
# спокойных отсчётов до признания веса устоявшимся.
STABLE_WINDOW_G = 2
STABLE_SAMPLES = 6
SAMPLE_PERIOD_S = 0.05


class FakeScale(ScaleDevice):
    def __init__(self, capacity_g: int = 15000) -> None:
        self.capacity_g = capacity_g
        self._target_g = 0.0  # «что лежит на платформе» — задаётся из симулятора в админке
        self._current_g = 0.0
        self._tare_g = 0
        self._stable_count = 0
        self._noise = 1.0
        self._task: asyncio.Task | None = None
        self._overload = False

    # --- управление симуляцией (используется только dev-эндпоинтами) ---
    def sim_put(self, grams: float) -> None:
        self._target_g = max(0.0, min(float(grams), self.capacity_g * 1.2))

    def sim_noise(self, noise: float) -> None:
        self._noise = max(0.0, float(noise))

    @property
    def sim_target_g(self) -> float:
        return self._target_g

    # --- ScaleDevice ---
    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _loop(self) -> None:
        while True:
            delta = self._target_g - self._current_g
            # экспоненциальное приближение + небольшой перелёт, как у реальной платформы
            self._current_g += delta * 0.35
            if abs(delta) > 5:
                self._current_g += random.uniform(-1, 1) * min(abs(delta) * 0.05, 8)
                self._stable_count = 0
            else:
                self._stable_count += 1
            self._overload = self._current_g > self.capacity_g
            await asyncio.sleep(SAMPLE_PERIOD_S)

    def read(self) -> WeightReading:
        noisy = self._current_g + random.uniform(-self._noise, self._noise)
        gross = int(round(noisy))
        stable = self._stable_count >= STABLE_SAMPLES and abs(
            self._current_g - self._target_g
        ) <= STABLE_WINDOW_G
        error = ScaleError.OVERLOAD if self._overload else None
        return WeightReading(gross_g=gross, tare_g=self._tare_g, stable=stable, error=error)

    async def tare(self) -> None:
        self._tare_g = int(round(self._current_g))

    async def zero(self) -> None:
        self._tare_g = 0
        self._target_g = 0.0
        self._current_g = 0.0
        self._stable_count = 0

    def status(self) -> DeviceStatus:
        return DeviceStatus(
            online=self._task is not None,
            kind="fake",
            detail={
                "capacity_g": self.capacity_g,
                "target_g": round(self._target_g, 1),
                "tare_g": self._tare_g,
                "overload": self._overload,
            },
        )
