"""Cableado de inyección del dominio app_platform."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.services.costo_canal_service import CostoCanalService
from app.core.database.session import get_db_session
from app.core.database.tenant_context import is_system_scope


def require_system_scope() -> None:
    """Solo el administrador del sistema entra al panel de app_platform.

    Hoy el alcance se fija explícito en el contexto (ver
    `tenant_context.py`); fase 04 (auth) lo conecta a la sesión real vía
    middleware, sin cambiar esta firma.
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


CostoCanalServiceDep = Annotated[CostoCanalService, Depends(get_costo_canal_service)]
