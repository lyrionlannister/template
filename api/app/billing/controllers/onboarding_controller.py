"""Pago único de onboarding."""

from fastapi import APIRouter, HTTPException, status

from app.app_platform.exceptions import ParametroComercialFaltanteError
from app.auth.dependencies import SesionActual
from app.auth.exceptions import PermisoInsuficienteError
from app.billing.dependencies import OnboardingServiceDep
from app.billing.exceptions import OnboardingYaPagadoError
from app.billing.schemas.onboarding_schema import (
    CobroRespuesta,
    OnboardingEstadoRespuesta,
    OnboardingPagarRequest,
)

router = APIRouter(prefix="/billing/onboarding", tags=["billing"])


@router.get("/estado", response_model=OnboardingEstadoRespuesta)
async def estado_onboarding(
    sesion: SesionActual, service: OnboardingServiceDep
) -> OnboardingEstadoRespuesta:
    pagado = await service.esta_pagado(sesion)
    return OnboardingEstadoRespuesta(pagado=pagado)


@router.post("", response_model=CobroRespuesta, status_code=status.HTTP_201_CREATED)
async def pagar_onboarding(
    body: OnboardingPagarRequest,
    sesion: SesionActual,
    service: OnboardingServiceDep,
) -> CobroRespuesta:
    try:
        cobro = await service.pagar(
            sesion, body.token, body.acceptance_token, body.accept_personal_auth
        )
    except OnboardingYaPagadoError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except PermisoInsuficienteError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except ParametroComercialFaltanteError as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, str(error)
        ) from error
    return CobroRespuesta.model_validate(cobro)
