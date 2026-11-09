"""Cableado de inyección del dominio audiences."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.audiences.repositories.audiencia_repository import AudienciaRepository
from app.audiences.services.audiencias_service import AudienciasService
from app.contacts.dependencies import get_contacts_service
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import get_db_session


def get_audiencias_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    contacts_service: Annotated[ContactsService, Depends(get_contacts_service)],
) -> AudienciasService:
    return AudienciasService(
        session,
        AudienciaRepository(session),
        contacts_service,
    )


AudienciasServiceDep = Annotated[AudienciasService, Depends(get_audiencias_service)]
