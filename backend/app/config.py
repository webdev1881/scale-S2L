"""Конфигурация сервиса. Всё переопределяется переменными окружения с префиксом S2L_."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LABELS_DIR = DATA_DIR / "labels"


class Settings(BaseSettings):
    # env_file обязан быть абсолютным: относительный путь pydantic резолвит от рабочего
    # каталога процесса, и при запуске uvicorn не из backend/ файл просто не находился.
    model_config = SettingsConfigDict(
        env_prefix="S2L_",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # fake — симулятор для разработки без весов, real — драйверы железа
    hal_backend: Literal["fake", "real"] = "fake"

    # Подтверждено на приборе: весовая плата висит на встроенном RS232, 19200 бод
    scale_port: str = "/dev/ttyS4"
    scale_baudrate: int = 19200
    printer_device: str = "/dev/usb/lp0"

    # Параметры весоизмерительной части Aurora S2 (6/15 кг, класс III): наибольший
    # предел, цена деления в двух диапазонах и наименьшая навеска. Сознательно живут
    # в конфиге устройства, а не в админке: это свойства прибора, и оператор торговой
    # точки менять их не должен.
    scale_capacity_g: int = 15000
    scale_division_g: int = 5  # выше scale_fine_range_g
    scale_fine_division_g: int = 2  # до scale_fine_range_g
    scale_fine_range_g: int = 6000
    scale_min_weight_g: int = 40

    db_url: str = f"sqlite:///{(DATA_DIR / 's2l.db').as_posix()}"
    host: str = "0.0.0.0"
    port: int = 8000

    # Частота публикации веса в WebSocket, Гц
    weight_stream_hz: float = 10.0


    @field_validator("db_url")
    @classmethod
    def _anchor_sqlite_path(cls, value: str) -> str:
        """Относительный путь в sqlite-URL считаем от каталога backend, а не от cwd.

        Иначе расположение базы зависит от того, откуда запущен uvicorn: из backend/,
        из корня репозитория или из systemd. SQLite вдобавок не создаёт недостающие
        каталоги и падает с невнятным "unable to open database file".
        """
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value
        rest = value[len(prefix) :]
        # sqlite:///:memory: и sqlite:////abs/path трогать нечего
        if not rest or rest.startswith(":memory:") or rest.startswith("/"):
            return value
        path = Path(rest)
        if path.is_absolute():
            return value
        return prefix + (BASE_DIR / path).resolve().as_posix()


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
