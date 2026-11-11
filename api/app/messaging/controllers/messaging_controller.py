"""Embedded Signup de WhatsApp (conexión del número del tenant) y envío
real de un mensaje de plantilla por Meta Cloud API."""

import httpx
from fastapi import APIRouter, HTTPException, status

from app.app_platform.exceptions import LimiteDePlanError
from app.auth.dependencies import SesionActual
from app.contacts.exceptions import ContactoNoEncontradoError
from app.messaging.dependencies import (
    ConexionWhatsappServiceDep,
    EnvioMensajeServiceDep,
)
from app.messaging.exceptions import (
    ConexionWhatsappNoEncontradaError,
    NumeroYaConectadoError,
    VariableFaltanteParaEnvioError,
)
from app.messaging.schemas.messaging_schema import (
    ConectarWhatsappRequest,
    ConexionWhatsappRespuesta,
    EnviarPlantillaRequest,
    EnvioPlantillaRespuesta,
)
from app.messaging.services.dispatcher_service import CanalSinProveedorError
from app.templates.exceptions import PlantillaNoEncontradaError

router = APIRouter(prefix="/messaging", tags=["messaging"])


@router.post(
    "/whatsapp/conectar",
    response_model=ConexionWhatsappRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def conectar_whatsapp(
    body: ConectarWhatsappRequest,
    sesion: SesionActual,
    service: ConexionWhatsappServiceDep,
) -> ConexionWhatsappRespuesta:
    try:
        conexion = await service.conectar(
            sesion, body.code, body.waba_id, body.phone_number_id
        )
    except NumeroYaConectadoError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except LimiteDePlanError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Meta rechazó el intercambio de autorización."
        ) from error
    return ConexionWhatsappRespuesta.model_validate(conexion)


@router.post("/plantillas/enviar", response_model=EnvioPlantillaRespuesta)
async def enviar_plantilla(
    body: EnviarPlantillaRequest,
    sesion: SesionActual,
    service: EnvioMensajeServiceDep,
) -> EnvioPlantillaRespuesta:
    try:
        resultado = await service.enviar_plantilla(
            body.plantilla_public_id, body.contacto_public_id
        )
    except (PlantillaNoEncontradaError, ContactoNoEncontradoError) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except VariableFaltanteParaEnvioError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    except (ConexionWhatsappNoEncontradaError, CanalSinProveedorError) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Meta rechazó el envío."
        ) from error
    return EnvioPlantillaRespuesta(message_id=resultado["messages"][0]["id"])
