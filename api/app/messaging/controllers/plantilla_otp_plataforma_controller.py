"""Plantilla de autenticación de WhatsApp de plataforma (OTP de login).
Gated por `require_system_scope` -- panel de administrador del sistema,
nunca una sesión de tenant."""

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_system_scope
from app.messaging.dependencies import PlantillaOtpPlataformaServiceDep
from app.messaging.exceptions import PlantillaOtpPlataformaNoEncontradaError
from app.messaging.schemas.messaging_schema import (
    PlantillaOtpPlataformaCrearRequest,
    PlantillaOtpPlataformaRespuesta,
)

router = APIRouter(
    prefix="/messaging/plataforma/plantilla-otp",
    tags=["messaging-plataforma"],
    dependencies=[Depends(require_system_scope)],
)


@router.post(
    "", response_model=PlantillaOtpPlataformaRespuesta, status_code=status.HTTP_201_CREATED
)
async def crear(
    body: PlantillaOtpPlataformaCrearRequest, service: PlantillaOtpPlataformaServiceDep
) -> PlantillaOtpPlataformaRespuesta:
    try:
        plantilla = await service.crear(body.nombre, body.idioma)
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Meta rechazó la creación de la plantilla."
        ) from error
    return PlantillaOtpPlataformaRespuesta.model_validate(plantilla)


@router.get("", response_model=list[PlantillaOtpPlataformaRespuesta])
async def listar(
    service: PlantillaOtpPlataformaServiceDep,
) -> list[PlantillaOtpPlataformaRespuesta]:
    plantillas = await service.listar()
    return [PlantillaOtpPlataformaRespuesta.model_validate(p) for p in plantillas]


@router.post(
    "/{public_id}/sincronizar", response_model=PlantillaOtpPlataformaRespuesta
)
async def sincronizar(
    public_id: UUID, service: PlantillaOtpPlataformaServiceDep
) -> PlantillaOtpPlataformaRespuesta:
    try:
        plantilla = await service.sincronizar_estado(public_id)
    except PlantillaOtpPlataformaNoEncontradaError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Meta rechazó la consulta de estado."
        ) from error
    return PlantillaOtpPlataformaRespuesta.model_validate(plantilla)
