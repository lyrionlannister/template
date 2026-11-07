"""Schemas Pydantic del panel de parámetros comerciales."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import field_serializer

from app.core.schemas.base_schema import BaseSchema


class ParametroComercialRegistrarRequest(BaseSchema):
    clave: str
    valor: Decimal
    fuente: str
    vigente_desde: date


class ParametroComercialRespuesta(BaseSchema):
    public_id: UUID
    clave: str
    valor: Decimal
    fuente: str
    vigente_desde: date
    vigente_hasta: date | None
    creado_en: datetime

    @field_serializer("valor")
    def _serializar_valor(self, valor: Decimal) -> str:
        return str(valor)
