"""Schemas de fuentes de pago recurrentes (suscripción)."""

from uuid import UUID

from app.core.schemas.base_schema import BaseSchema


class IniciarFuenteDePagoRequest(BaseSchema):
    token: str
    acceptance_token: str
    accept_personal_auth: str
    # Datos de visualización (marca, últimos 4, vencimiento): ya vienen en la
    # respuesta de tokenización que el navegador recibió de Wompi, nunca del
    # número completo ni el CVC.
    marca: str | None = None
    ultimos_cuatro: str | None = None
    mes_expiracion: str | None = None
    anio_expiracion: str | None = None


class FuenteDePagoRespuesta(BaseSchema):
    public_id: UUID
    estado: str


class TarjetaRespuesta(BaseSchema):
    marca: str | None
    ultimos_cuatro: str | None
    mes_expiracion: str | None
    anio_expiracion: str | None


class EstadoFuenteDePagoRespuesta(BaseSchema):
    estado: str
    paso_actual: str | None
    iframe_html: str | None


class TokensDeAceptacionRespuesta(BaseSchema):
    acceptance_token: str
    accept_personal_auth: str
    permalink_aceptacion: str
    permalink_datos: str
