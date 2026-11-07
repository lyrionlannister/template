"""Fuentes de pago recurrentes: preautorización con 3DS para la suscripción."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.app_platform.exceptions import LimiteDePlanError
from app.auth.dependencies import SesionActual
from app.billing.dependencies import FuenteDePagoServiceDep, WompiClientDep
from app.billing.schemas.fuente_de_pago_schema import (
    EstadoFuenteDePagoRespuesta,
    FuenteDePagoRespuesta,
    IniciarFuenteDePagoRequest,
    TokensDeAceptacionRespuesta,
)
from app.billing.services.fuente_de_pago_service import FuenteDePagoNoEncontradaError

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/tokens-aceptacion", response_model=TokensDeAceptacionRespuesta)
async def tokens_de_aceptacion(
    _sesion: SesionActual, wompi_client: WompiClientDep
) -> TokensDeAceptacionRespuesta:
    """Proxy de `GET /merchants/info`: Wompi no habilita CORS ahí, así que el
    navegador no puede pedirlo directo (ver `client/src/billing/`)."""

    tokens = await wompi_client.obtener_tokens_de_aceptacion()
    presigned_aceptacion = tokens["data"]["presigned_acceptance"]
    presigned_datos = tokens["data"]["presigned_personal_data_auth"]
    return TokensDeAceptacionRespuesta(
        acceptance_token=presigned_aceptacion["acceptance_token"],
        accept_personal_auth=presigned_datos["acceptance_token"],
        permalink_aceptacion=presigned_aceptacion["permalink"],
        permalink_datos=presigned_datos["permalink"],
    )


@router.post(
    "/fuentes-de-pago",
    response_model=FuenteDePagoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def iniciar_fuente_de_pago(
    body: IniciarFuenteDePagoRequest,
    sesion: SesionActual,
    service: FuenteDePagoServiceDep,
) -> FuenteDePagoRespuesta:
    try:
        fuente = await service.iniciar_preautorizacion(
            sesion,
            body.token,
            body.acceptance_token,
            body.accept_personal_auth,
            marca=body.marca,
            ultimos_cuatro=body.ultimos_cuatro,
            mes_expiracion=body.mes_expiracion,
            anio_expiracion=body.anio_expiracion,
        )
    except LimiteDePlanError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return FuenteDePagoRespuesta(public_id=fuente.public_id, estado=fuente.estado.value)


@router.get(
    "/fuentes-de-pago/{public_id}/estado", response_model=EstadoFuenteDePagoRespuesta
)
async def estado_fuente_de_pago(
    public_id: UUID, sesion: SesionActual, service: FuenteDePagoServiceDep
) -> EstadoFuenteDePagoRespuesta:
    try:
        estado = await service.consultar_estado(sesion, public_id)
    except FuenteDePagoNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return EstadoFuenteDePagoRespuesta(
        estado=estado["estado"],
        paso_actual=estado["pasoActual"],
        iframe_html=estado["iframeHtml"],
    )
