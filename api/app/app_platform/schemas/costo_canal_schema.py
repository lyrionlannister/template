"""Schemas Pydantic del panel de costos por canal.

`costo_unitario` serializa como `str`, nunca `float` ni `Decimal` crudo en
JSON (ver skill `money-precision`).
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import field_serializer

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.core.schemas.base_schema import BaseSchema


class RegistrarCostoCanalRequest(BaseSchema):
    canal: CanalMensajeria
    categoria: CategoriaMensaje | None = None
    proveedor: str
    costo_unitario: Decimal
    moneda: str
    vigente_desde: date
    fuente: str


class CostoCanalRespuesta(BaseSchema):
    public_id: UUID
    canal: CanalMensajeria
    categoria: CategoriaMensaje | None
    proveedor: str
    costo_unitario: Decimal
    moneda: str
    vigente_desde: date
    vigente_hasta: date | None
    fuente: str
    creado_en: datetime

    @field_serializer("costo_unitario")
    def _serializar_costo(self, valor: Decimal) -> str:
        return str(valor)
