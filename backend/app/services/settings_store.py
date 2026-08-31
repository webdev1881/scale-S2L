"""Настройки устройства: одна JSON-строка в БД, правится из админки без рестарта."""
from __future__ import annotations

import json

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models import AppSetting

SETTINGS_KEY = "device"


class DeviceSettings(BaseModel):
    store_name: str = "Маркет «Весна»"
    currency: str = "₴"
    label_width_mm: float = 60
    label_height_mm: float = 40
    # Шаблон весового EAN-13: P — цифра PLU, W — цифра значения
    barcode_template: str = "22PPPPPWWWWW"
    # weight — в штрихкод уходит масса в граммах, total — сумма в копейках
    barcode_value: str = Field(default="weight", pattern="^(weight|total)$")
    min_print_weight_g: int = 5
    require_stable: bool = True
    # Сколько секунд бездействия до сброса экрана киоска
    kiosk_idle_reset_s: int = 45


def load_settings(db: Session) -> DeviceSettings:
    row = db.get(AppSetting, SETTINGS_KEY)
    if row is None or not row.value:
        return DeviceSettings()
    try:
        return DeviceSettings.model_validate(json.loads(row.value))
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
