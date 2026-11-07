"""Schemas de la suscripción mensual."""

from datetime import date
from decimal import Decimal

from pydantic import field_serializer

from app.billing.schemas.fuente_de_pago_schema import TarjetaRespuesta
from app.core.schemas.base_schema import BaseSchema


class SuscripcionEstadoRespuesta(BaseSchema):
    existe: bool
    estado: str | None
    monto_cop: Decimal | None
    proxima_fecha_cobro: date | None
    tarjeta: TarjetaRespuesta | None

    @field_serializer("monto_cop")
    def _serializar_monto(self, valor: Decimal | None) -> str | None:
        return str(valor) if valor is not None else None
