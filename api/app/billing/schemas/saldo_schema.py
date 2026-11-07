"""Schemas de recarga y consulta de saldo utilizable."""

from decimal import Decimal
from uuid import UUID

from pydantic import field_serializer

from app.core.schemas.base_schema import BaseSchema


class RecargarTarjetaRequest(BaseSchema):
    monto_cop: int
    token: str
    acceptance_token: str
    accept_personal_auth: str


class RecargarPseRequest(BaseSchema):
    monto_cop: int
    user_type: int
    user_legal_id_type: str
    user_legal_id: str
    financial_institution_code: str


class RecargarNequiRequest(BaseSchema):
    monto_cop: int
    phone_number: str


class MovimientoSaldoRespuesta(BaseSchema):
    public_id: UUID
    estado: str
    medio: str | None
    monto_cop: Decimal
    referencia: str

    @field_serializer("monto_cop")
    def _serializar_monto(self, valor: Decimal) -> str:
        return str(valor)


class RecargaPseRespuesta(BaseSchema):
    movimiento: MovimientoSaldoRespuesta
    async_payment_url: str | None


class InstitucionFinancieraRespuesta(BaseSchema):
    code: str
    name: str


class SaldoEstadoRespuesta(BaseSchema):
    saldo_cop: Decimal
    movimientos: list[MovimientoSaldoRespuesta]

    @field_serializer("saldo_cop")
    def _serializar_saldo(self, valor: Decimal) -> str:
        return str(valor)
