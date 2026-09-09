"""Симулятор весовой платы.

Имитирует то, что портит жизнь в реальности: качание платформы под положенным
грузом, шум АЦП, ползучесть датчика и задержку стабилизации. UI обязан корректно вести себя с «дрожащим» весом ещё до встречи с железом.
"""
from __future__ import annotations

import asyncio
import math
import random
from collections import deque

from ...errors import ScaleError
from ..base import DeviceStatus, ScaleDevice, WeightReading

# Порог, внутри которого вес считается неподвижным, и число подряд идущих
# спокойных отсчётов до признания веса устоявшимся.
STABLE_WINDOW_G = 2
STABLE_SAMPLES = 8
SAMPLE_PERIOD_S = 0.02

# Платформа на тензодатчике — пружина с грузом: положенный товар проскакивает
# нужное значение и качается вокруг него, затухая. Собственная частота у весов
# этого класса — единицы герц, затухание неполное, поэтому видно два-три колебания.
RESONANCE_HZ = 2.6
# 0.5 даёт перелёт около 15% — столько и видно на настоящей платформе. Меньше
# затухание — платформа болтается неправдоподобно долго, больше — груз «доезжает»
# по прямой, и проверять на симуляторе становится нечего.
DAMPING = 0.5
# Ползучесть тензодатчика под нагрузкой: показание ещё несколько секунд ползёт на
# доли грамма. Держим её ниже порога покоя, иначе весы никогда бы не устоялись.
CREEP_G = 1.2
CREEP_TAU_S = 3.0


class FakeScale(ScaleDevice):
    def __init__(
        self,
        capacity_g: int = 15000,
        division_g: int = 5,
        fine_division_g: int = 2,
        fine_range_g: int = 6000,
    ) -> None:
        self.capacity_g = capacity_g
        self.division_g = division_g
        self.fine_division_g = fine_division_g
        self.fine_range_g = fine_range_g
        self._target_g = 0.0  # «что лежит на платформе» — задаётся из симулятора в админке
        self._current_g = 0.0
        self._velocity = 0.0  # скорость колебания платформы, г/с
        self._creep_g = 0.0  # набежавшая ползучесть датчика
        self._tare_g = 0
        self._stable_count = 0
        self._noise = 1.0
        # Окно недавних отсчётов: покой определяется по их разбросу, а не по
        # близости к цели — настоящая плата тоже не знает, что на неё положили.
        self._history: deque[float] = deque(maxlen=STABLE_SAMPLES)
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
        omega = 2 * math.pi * RESONANCE_HZ
        while True:
            dt = SAMPLE_PERIOD_S
            # Груз на пружине: ускорение тянет к цели, затухание гасит колебание.
            # Отсюда и перелёт, и качание вокруг нужного значения, и полторы секунды
            # до покоя — то, чего покупатель ждёт у платформы.
            accel = omega * omega * (self._target_g - self._current_g)
            accel -= 2 * DAMPING * omega * self._velocity
            self._velocity += accel * dt
            self._current_g += self._velocity * dt

            # Ползучесть догоняет нагрузку по экспоненте и живёт отдельно от колебания.
            цель_ползучести = CREEP_G if self._target_g > 0 else 0.0
            self._creep_g += (цель_ползучести - self._creep_g) * dt / CREEP_TAU_S

            # Шум АЦП в состояние не подмешиваем: он живёт в самом отсчёте (`read`).
            # Подмешанный сюда, он превращался в случайное блуждание, разброс окна
            # не сходился, и признак покоя мигал туда-сюда у самого порога.
            self._history.append(self._current_g + self._creep_g)
            спокойно = len(self._history) == self._history.maxlen and (
                max(self._history) - min(self._history) <= STABLE_WINDOW_G
            )
            self._stable_count = self._stable_count + 1 if спокойно else 0

            # Перегрузка объявляется на 9 делений выше НПВ, как требует OIML R76
            self._overload = self._current_g > self.capacity_g + 9 * self.division_g
            await asyncio.sleep(dt)

    def division_for(self, grams: float) -> int:
        """Двухдиапазонная цена деления: до 6 кг — 2 г, выше — 5 г."""
        return self.fine_division_g if abs(grams) <= self.fine_range_g else self.division_g

    def read(self) -> WeightReading:
        noisy = self._current_g + self._creep_g + random.uniform(-self._noise, self._noise)
        # Реальная плата не отдаёт произвольные граммы: показание всегда кратно цене
        # деления. Иначе на этикетке появится вес, который прибор измерить не может.
        step = self.division_for(noisy)
        gross = int(round(noisy / step) * step)
        stable = self._stable_count >= STABLE_SAMPLES
        error = ScaleError.OVERLOAD if self._overload else None
        return WeightReading(gross_g=gross, tare_g=self._tare_g, stable=stable, error=error)

    async def tare(self) -> None:
        self._tare_g = int(round(self._current_g))

    async def zero(self) -> None:
        self._tare_g = 0
        self._target_g = 0.0
        self._current_g = 0.0
        self._velocity = 0.0
        self._creep_g = 0.0
        self._stable_count = 0
        self._history.clear()

    def status(self) -> DeviceStatus:
        return DeviceStatus(
            online=self._task is not None,
            kind="fake",
            detail={
                "capacity_g": self.capacity_g,
                "division_g": self.division_g,
                "fine_division_g": self.fine_division_g,
                "fine_range_g": self.fine_range_g,
                "target_g": round(self._target_g, 1),
                "tare_g": self._tare_g,
                "overload": self._overload,
            },
        )
