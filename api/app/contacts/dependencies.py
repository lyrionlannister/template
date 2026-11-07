"""Cableado de inyección del dominio contacts."""

from typing import Annotated

from fastapi import Depends

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
from app.contacts.services.contacts_service import ContactsService


def get_contacts_service(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
    parametro_comercial_service: Annotated[
        ParametroComercialService, Depends(get_parametro_comercial_service)
    ],
) -> ContactsService:
    return ContactsService(auth_service, plan_service, parametro_comercial_service)


ContactsServiceDep = Annotated[ContactsService, Depends(get_contacts_service)]
