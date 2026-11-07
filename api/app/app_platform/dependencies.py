"""Cableado de inyección del dominio app_platform."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.pool_incluidos_service import PoolIncluidosService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.core.database.session import get_db_session
from app.core.database.tenant_context import is_system_scope


def require_system_scope() -> None:
    """Solo el administrador del sistema entra al panel de app_platform.

    Hoy el alcance se fija explícito en el contexto (ver
    `tenant_context.py`); el auth de fase 04 todavía no tiene identidad de
    administrador del sistema (solo usuarios de tenant), así que esto sigue
    sin estar conectado a una sesión real. Queda pendiente para cuando
    exista esa identidad, sin cambiar esta firma.
    """

    if not is_system_scope():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere alcance de administrador del sistema.",
        )


def get_costo_canal_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CostoCanalService:
    return CostoCanalService(session)


def get_tipo_cambio_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TipoCambioService:
    return TipoCambioService(session)


def get_parametro_comercial_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ParametroComercialService:
    return ParametroComercialService(session)


def get_plan_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    costo_canal_service: Annotated[CostoCanalService, Depends(get_costo_canal_service)],
    tipo_cambio_service: Annotated[TipoCambioService, Depends(get_tipo_cambio_service)],
    parametro_comercial_service: Annotated[
        ParametroComercialService, Depends(get_parametro_comercial_service)
    ],
) -> PlanService:
    return PlanService(
        session, costo_canal_service, tipo_cambio_service, parametro_comercial_service
    )


def get_pool_incluidos_service() -> PoolIncluidosService:
    return PoolIncluidosService()


CostoCanalServiceDep = Annotated[CostoCanalService, Depends(get_costo_canal_service)]
TipoCambioServiceDep = Annotated[TipoCambioService, Depends(get_tipo_cambio_service)]
ParametroComercialServiceDep = Annotated[
    ParametroComercialService, Depends(get_parametro_comercial_service)
]
PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
PoolIncluidosServiceDep = Annotated[
    PoolIncluidosService, Depends(get_pool_incluidos_service)
]
