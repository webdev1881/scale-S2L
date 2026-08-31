"""Конфигурация сервиса. Всё переопределяется переменными окружения с префиксом S2L_."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LABELS_DIR = DATA_DIR / "labels"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="S2L_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # fake — симулятор для разработки без весов, real — драйверы железа
    hal_backend: Literal["fake", "real"] = "fake"

    scale_port: str = "/dev/serial/by-id/CHANGE-ME"
    scale_baudrate: int = 9600
    printer_device: str = "/dev/usb/lp0"

    db_url: str = f"sqlite:///{(DATA_DIR / 's2l.db').as_posix()}"
    host: str = "0.0.0.0"
    port: int = 8000

    # Частота публикации веса в WebSocket, Гц
    weight_stream_hz: float = 10.0


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
