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
# Снимки, пришедшие на прибор извне (выгрузка из 1С). Лежат в данных, а не в сборке
# фронта: сборка внутри docker-образа переписывается при каждом обновлении, а
# каталог `data/` — том, который переживает пересоздание контейнера и переносится
# на новый прибор вместе с базой.
PHOTOS_DIR = DATA_DIR / "photos"
# Собранный фронт. Здесь, а не в main.py: его время сборки — это и версия ПО
# прибора, которую показывает админка (`/api/updated-at`).
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
# Настройки прибора лежат отдельным файлом: их удобно посмотреть, положить
# в резервную копию и подложить на новый прибор, не трогая базу.
SETTINGS_FILE = DATA_DIR / "settings.json"
# Образец настроек из репозитория: с него начинается прибор, у которого своего
# файла ещё нет. Сам `settings.json` в гите не лежит — он у каждого свой.
SETTINGS_EXAMPLE_FILE = DATA_DIR / "settings.example.json"
# Именованные снимки настроек — переключиться между «залом» и «прилавком» одной
# кнопкой в шапке, не подбирая заново десяток полей. Отдельный файл рядом с
# основными настройками по той же причине, что и они сами.
SETTINGS_PRESETS_FILE = DATA_DIR / "settings_presets.json"


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
    # Демо-каталог в пустую базу (только на симуляторе). Выключают, когда пустая
    # база нужна по делу — например, под выгрузку из 1С (tools/mock_data.py).
    seed_demo: bool = True

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

    # Токен для приёма выгрузки каталога из 1С (POST /api/catalog/1c-import,
    # заголовок X-API-Key: <токен>, как шлёт обработка 1С). Пусто — приём выключен.
    import_token: str = ""

    # Логин и пароль админки (HTTP Basic, см. app/auth.py). Пустой пароль —
    # админка открыта; так удобно на машине разработчика и опасно на приборе,
    # который смотрит в интернет через туннель.
    admin_user: str = "admin"
    admin_password: str = ""

    # Версия прибора: проставляются при сборке образа (см. Dockerfile), на
    # машине разработчика пусты — тогда версией считается время сборки фронта.
    build_sha: str = ""
    build_at: str = ""


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
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
