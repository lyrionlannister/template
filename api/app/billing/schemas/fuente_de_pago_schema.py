"""Schemas de fuentes de pago recurrentes (suscripción)."""

from uuid import UUID

from app.core.schemas.base_schema import BaseSchema


class IniciarFuenteDePagoRequest(BaseSchema):
    token: str
    acceptance_token: str
    accept_personal_auth: str


class FuenteDePagoRespuesta(BaseSchema):
    public_id: UUID
    estado: str


class EstadoFuenteDePagoRespuesta(BaseSchema):
    estado: str
    paso_actual: str | None
    iframe_html: str | None


class TokensDeAceptacionRespuesta(BaseSchema):
    acceptance_token: str
    accept_personal_auth: str
    permalink_aceptacion: str
    permalink_datos: str
