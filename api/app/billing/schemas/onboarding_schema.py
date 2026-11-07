"""Schemas del pago de onboarding. El backend nunca recibe el número de
tarjeta: `token` ya viene de tokenizar en el navegador contra la pasarela con
la llave pública (ver `client/src/billing/`)."""

from decimal import Decimal

from pydantic import field_serializer

from app.billing.enums.billing_enums import EstadoTransaccionPago
from app.core.schemas.base_schema import BaseSchema


class OnboardingPagarRequest(BaseSchema):
    token: str
    acceptance_token: str
    accept_personal_auth: str


class OnboardingEstadoRespuesta(BaseSchema):
    pagado: bool
    precio_cop: Decimal

    @field_serializer("precio_cop")
    def _serializar_precio(self, valor: Decimal) -> str:
        return str(valor)


class CobroRespuesta(BaseSchema):
    estado: EstadoTransaccionPago
    monto_cop: Decimal
    referencia: str

    @field_serializer("monto_cop")
    def _serializar_monto(self, valor: Decimal) -> str:
        return str(valor)
