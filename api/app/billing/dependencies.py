"""Cableado de inyección del dominio billing."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.dependencies import (
    get_parametro_comercial_service,
    get_plan_service,
)
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.auth.dependencies import get_auth_service
from app.auth.services.auth_service import AuthService
from app.billing.clients.wompi_client import WompiClient
from app.billing.services.evento_pago_service import EventoPagoService
from app.billing.services.fuente_de_pago_service import FuenteDePagoService
from app.billing.services.onboarding_service import OnboardingService
from app.billing.services.suscripcion_service import SuscripcionService
from app.core.database.session import get_db_session


async def get_wompi_client() -> AsyncGenerator[WompiClient]:
    cliente = WompiClient()
    try:
        yield cliente
    finally:
        await cliente.cerrar()


WompiClientDep = Annotated[WompiClient, Depends(get_wompi_client)]


def get_evento_pago_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    parametro_comercial_service: Annotated[
        ParametroComercialService, Depends(get_parametro_comercial_service)
    ],
) -> EventoPagoService:
    return EventoPagoService(session, auth_service, parametro_comercial_service)


def get_suscripcion_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    wompi_client: WompiClientDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
) -> SuscripcionService:
    return SuscripcionService(session, wompi_client, auth_service, plan_service)


def get_onboarding_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    parametro_comercial_service: Annotated[
        ParametroComercialService, Depends(get_parametro_comercial_service)
    ],
    wompi_client: WompiClientDep,
) -> OnboardingService:
    return OnboardingService(
        session, auth_service, parametro_comercial_service, wompi_client
    )


def get_fuente_de_pago_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    wompi_client: WompiClientDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
    suscripcion_service: Annotated[
        SuscripcionService, Depends(get_suscripcion_service)
    ],
) -> FuenteDePagoService:
    return FuenteDePagoService(
        session, wompi_client, auth_service, plan_service, suscripcion_service
    )


EventoPagoServiceDep = Annotated[EventoPagoService, Depends(get_evento_pago_service)]
OnboardingServiceDep = Annotated[OnboardingService, Depends(get_onboarding_service)]
SuscripcionServiceDep = Annotated[SuscripcionService, Depends(get_suscripcion_service)]
FuenteDePagoServiceDep = Annotated[
    FuenteDePagoService, Depends(get_fuente_de_pago_service)
]
