"""Cableado de inyección del dominio billing."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.services.evento_pago_service import EventoPagoService
from app.core.database.session import get_db_session


def get_evento_pago_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EventoPagoService:
    return EventoPagoService(session)


EventoPagoServiceDep = Annotated[EventoPagoService, Depends(get_evento_pago_service)]
