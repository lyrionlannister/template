"""Schemas Pydantic del panel de planes. Los montos en COP serializan como
`str`, nunca `float` ni `Decimal` crudo (ver skill `money-precision`)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import field_serializer

from app.core.schemas.base_schema import BaseSchema


class PlanRequest(BaseSchema):
    nombre: str
    precio_mensual_cop: Decimal
    limite_filas_importacion: int
    mensajes_marketing_incluidos: int
    precio_marketing_mensaje_cop: Decimal
    precio_utility_mensaje_cop: Decimal
    max_usuarios: int
    max_whatsapp_numeros: int


class PlanActualizarRequest(BaseSchema):
    nombre: str | None = None
    precio_mensual_cop: Decimal | None = None
    limite_filas_importacion: int | None = None
    mensajes_marketing_incluidos: int | None = None
    precio_marketing_mensaje_cop: Decimal | None = None
    precio_utility_mensaje_cop: Decimal | None = None
    max_usuarios: int | None = None
    max_whatsapp_numeros: int | None = None


class PlanRespuesta(BaseSchema):
    public_id: UUID
    nombre: str
    precio_mensual_cop: Decimal
    limite_filas_importacion: int
    mensajes_marketing_incluidos: int
    precio_marketing_mensaje_cop: Decimal
    precio_utility_mensaje_cop: Decimal
    max_usuarios: int
    max_whatsapp_numeros: int
    creado_en: datetime

    @field_serializer(
        "precio_mensual_cop",
        "precio_marketing_mensaje_cop",
        "precio_utility_mensaje_cop",
    )
    def _serializar_monto(self, valor: Decimal) -> str:
        return str(valor)
