"""Выбор реализации железа по конфигу. Единственное место, где fake встречается с real."""
from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
from .base import PrinterDevice, ScaleDevice
from .printer.fake import FakePrinter
from .printer.usb_raw import UsbRawPrinter
from .scale.fake import FakeScale
from .scale.serial_scale import SerialScale


@dataclass
class Devices:
    scale: ScaleDevice
    printer: PrinterDevice
    backend: str

    @property
    def is_fake(self) -> bool:
        return self.backend == "fake"


_devices: Devices | None = None


def build_devices(settings: Settings) -> Devices:
    if settings.hal_backend == "real":
        return Devices(
            scale=SerialScale(settings.scale_port, settings.scale_baudrate),
            printer=UsbRawPrinter(settings.printer_device),
            backend="real",
        )
    return Devices(
        scale=FakeScale(
            capacity_g=settings.scale_capacity_g,
            division_g=settings.scale_division_g,
            fine_division_g=settings.scale_fine_division_g,
            fine_range_g=settings.scale_fine_range_g,
        ),
        printer=FakePrinter(),
        backend="fake",
    )


def set_devices(devices: Devices) -> None:
    global _devices
    _devices = devices


def get_devices() -> Devices:
    if _devices is None:
        raise RuntimeError("Устройства не инициализированы")
    return _devices
