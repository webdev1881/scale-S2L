"""Отметки о том, когда прибор последний раз что-то принял.

Отдельный файл `data/state.json`, а не поле в настройках: настройки админка
шлёт целиком, и время последней выгрузки из 1С, попав в ту же модель, затиралось
бы при каждом сохранении формы — оператор открыл страницу утром, нажал
«Зберегти» вечером и вернул бы утреннюю отметку.

Файл маленький и переживает перезапуск; потеряется — не беда, отметки появятся
снова при следующей выгрузке.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from ..config import DATA_DIR

STATE_FILE = DATA_DIR / "state.json"


def read() -> dict[str, Any]:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def mark(key: str, **extra: Any) -> None:
    """Записывает «это случилось сейчас» плюс, если надо, пару чисел рядом."""
    state = read()
    state[key] = {"at": datetime.now().isoformat(timespec="seconds"), **extra}
    _write(state)


def _write(state: dict[str, Any]) -> None:
    # Атомарно, тем же приёмом, что и настройки: обесточивание в момент записи
    # не должно оставить обрезанный JSON.
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, STATE_FILE)
