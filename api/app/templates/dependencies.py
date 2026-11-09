"""Cableado de inyección del dominio templates."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.audiences.dependencies import get_audiencias_service
from app.audiences.services.audiencias_service import AudienciasService
from app.contacts.dependencies import get_contacts_service
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import get_db_session
from app.templates.repositories.plantilla_repository import PlantillaRepository
from app.templates.services.templates_service import TemplatesService


def get_templates_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    contacts_service: Annotated[ContactsService, Depends(get_contacts_service)],
    audiencias_service: Annotated[AudienciasService, Depends(get_audiencias_service)],
) -> TemplatesService:
    return TemplatesService(
        session,
        PlantillaRepository(session),
        contacts_service,
        audiencias_service,
    )


TemplatesServiceDep = Annotated[TemplatesService, Depends(get_templates_service)]
