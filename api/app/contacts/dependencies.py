"""Cableado de inyección del dominio contacts."""

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
from app.contacts.repositories.configuracion_contactos_repository import (
    ConfiguracionContactosRepository,
)
from app.contacts.repositories.conflicto_variable_repository import (
    ConflictoVariableRepository,
)
from app.contacts.repositories.contacto_rechazado_repository import (
    ContactoRechazadoRepository,
)
from app.contacts.repositories.contacto_repository import ContactoRepository
from app.contacts.repositories.importacion_contacto_repository import (
    ImportacionContactoRepository,
)
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import get_db_session


def get_contacts_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
    parametro_comercial_service: Annotated[
        ParametroComercialService, Depends(get_parametro_comercial_service)
    ],
) -> ContactsService:
    return ContactsService(
        session,
        auth_service,
        plan_service,
        parametro_comercial_service,
        ContactoRepository(session),
        ImportacionContactoRepository(session),
        ConfiguracionContactosRepository(session),
        ConflictoVariableRepository(session),
        ContactoRechazadoRepository(session),
    )


ContactsServiceDep = Annotated[ContactsService, Depends(get_contacts_service)]
