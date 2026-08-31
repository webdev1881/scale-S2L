"""Контракты слоя абстракции железа.

Весь остальной код знает только эти интерфейсы. Драйверы (fake/real) взаимозаменяемы,
поэтому UI и бизнес-логика разрабатываются и тестируются без физических весов.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WeightReading:
    """Один отсчёт весовой платы."""

    gross_g: int  # брутто, как отдаёт плата
    tare_g: int  # текущая тара
    stable: bool  # вес устоялся — только тогда разрешена печать
    error: str | None = None

    @property
    def net_g(self) -> int:
        return self.gross_g - self.tare_g


@dataclass
class PrintJob:
    """Готовое к печати задание: растр этикетки + команды принтера."""

    name: str
    width_px: int
    height_px: int
    png_bytes: bytes
    tspl: bytes


@dataclass
class DeviceStatus:
    online: bool
    kind: str  # fake | real
    detail: dict[str, Any] = field(default_factory=dict)


class ScaleDevice(abc.ABC):
    """Весовая плата."""

    @abc.abstractmethod
    async def start(self) -> None: ...

    @abc.abstractmethod
    async def stop(self) -> None: ...

    @abc.abstractmethod
    def read(self) -> WeightReading:
        """Последний известный отсчёт. Не блокирует — драйвер опрашивает порт фоном."""

    @abc.abstractmethod
    async def tare(self) -> None: ...

    @abc.abstractmethod
    async def zero(self) -> None: ...

    @abc.abstractmethod
    def status(self) -> DeviceStatus: ...


class PrinterDevice(abc.ABC):
    """Принтер этикеток."""

    @abc.abstractmethod
    async def start(self) -> None: ...

    @abc.abstractmethod
    async def stop(self) -> None: ...

    @abc.abstractmethod
    async def print_label(self, job: PrintJob) -> str:
        """Печатает задание. Возвращает имя файла превью (fake) или '' (real)."""

    @abc.abstractmethod
    def status(self) -> DeviceStatus: ...
