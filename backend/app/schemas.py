from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductIn(BaseModel):
    plu: int = Field(ge=1, le=99999)
    name: str = Field(min_length=1, max_length=120)
    unit: str = Field(default="weight", pattern="^(weight|piece)$")
    price: float = Field(ge=0)
    category: str = ""
    tare_g: int = Field(default=0, ge=0)
    shelf_life_days: int = Field(default=0, ge=0)
    composition: str = ""
    emoji: str = ""
    active: int = 1


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class WeightOut(BaseModel):
    gross_g: int
    net_g: int
    tare_g: int
    stable: bool
    error: str | None = None


class DeviceStatusOut(BaseModel):
    online: bool
    kind: str
    detail: dict


class StatusOut(BaseModel):
    backend: str
    scale: DeviceStatusOut
    printer: DeviceStatusOut


class PrintRequest(BaseModel):
    product_id: int
    # Если не передан — берётся текущий нетто с весов (обычный сценарий киоска)
    weight_g: int | None = Field(default=None, ge=0)
    copies: int = Field(default=1, ge=1, le=5)


class PrintResult(BaseModel):
    transaction_id: int
    barcode: str
    weight_g: int
    total: float
    label_url: str | None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    product_id: int
    product_name: str
    weight_g: int
    price: float
    total: float
    barcode: str
    label_file: str


class SimWeightIn(BaseModel):
    grams: float = Field(ge=0, le=20000)


class SimPrinterIn(BaseModel):
    paper_out: bool | None = None
    cover_open: bool | None = None


class LabelPreviewRequest(BaseModel):
    product_id: int
    weight_g: int = Field(default=0, ge=0)
