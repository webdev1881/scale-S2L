"""Настройки устройства: одна JSON-строка в БД, правится из админки без рестарта."""
from __future__ import annotations

import json

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models import AppSetting

SETTINGS_KEY = "device"


class DeviceSettings(BaseModel):
    # Язык киоска, админки и печатной этикетки. Переключается в настройках админки.
    language: str = Field(default="uk", pattern="^(uk|ru)$")
    # Тема киоска. Тёмная по умолчанию: экран прибора светит покупателю в лицо
    # весь день, и белая заливка на 15.6" утомляет сильнее.
    theme: str = Field(default="dark", pattern="^(dark|light)$")
    store_name: str = "Рулька"
    currency: str = "₴"
    # Печатающий узел Aurora S2 берёт ленту шириной не более 56 мм
    label_width_mm: float = Field(default=56, ge=20, le=56)
    label_height_mm: float = Field(default=40, ge=20, le=120)
    # Шаблон весового EAN-13: P — цифра PLU, W — цифра значения
    barcode_template: str = "22PPPPPWWWWW"
    # weight — в штрихкод уходит масса в граммах, total — сумма в копейках
    barcode_value: str = Field(default="weight", pattern="^(weight|total)$")
    # Наименьшая навеска прибора — 40 г, ниже взвешивать нельзя
    min_print_weight_g: int = 40
    require_stable: bool = True
    # Сколько секунд бездействия до сброса экрана киоска
    kiosk_idle_reset_s: int = 45
    # Длительность стартовой заставки. 0 — не показывать её вовсе.
    splash_seconds: float = Field(default=3.0, ge=0, le=10)

    # Масштабы подписей и доля высоты карточки под фотографию. Экран прибора стоит
    # от покупателя дальше, чем монитор от разработчика, и подходящий размер
    # подбирается на месте, а не подгоняется в вёрстке.
    ui_scale_weight: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_group_title: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_product_name: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_product_price: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_product_code: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_scale_footer: float = Field(default=1.0, ge=0.7, le=2.0)
    ui_photo_group: int = Field(default=60, ge=30, le=85)
    ui_photo_product: int = Field(default=60, ge=30, le=85)
    # Сетка каталога: столбцов x строк на страницу. Подбирается под диагональ экрана,
    # поэтому вынесено в настройки, а не зашито в вёрстку.
    # 4x2 подобрано под экран Aurora S2 (15.6", 1366x768): при трёх рядах карточка
    # сжимается до 131 px и фото товара перестаёт читаться.
    grid_cols: int = Field(default=4, ge=2, le=6)
    grid_rows: int = Field(default=2, ge=1, le=5)


def load_settings(db: Session) -> DeviceSettings:
    row = db.get(AppSetting, SETTINGS_KEY)
    if row is None or not row.value:
        return DeviceSettings()
    try:
        data = json.loads(row.value)
        # Ширина этикетки могла быть сохранена до того, как появился предел принтера.
        # Подрезаем её, а не роняем всю запись в дефолты.
        if isinstance(data, dict) and isinstance(data.get("label_width_mm"), (int, float)):
            data["label_width_mm"] = min(float(data["label_width_mm"]), 56)
        return DeviceSettings.model_validate(data)
    except (ValueError, json.JSONDecodeError):
        # Битая запись не должна ронять киоск — откатываемся на значения по умолчанию.
        return DeviceSettings()


def save_settings(db: Session, settings: DeviceSettings) -> DeviceSettings:
    row = db.get(AppSetting, SETTINGS_KEY)
    payload = json.dumps(settings.model_dump(), ensure_ascii=False)
    if row is None:
        db.add(AppSetting(key=SETTINGS_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    return settings
