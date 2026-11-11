"""Cableado de inyección del dominio messaging."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.dependencies import get_plan_service
from app.app_platform.services.plan_service import PlanService
from app.auth.dependencies import get_auth_service
from app.auth.services.auth_service import AuthService
from app.contacts.dependencies import get_contacts_service
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import get_db_session
from app.messaging.clients.meta_client import MetaClient
from app.messaging.clients.sent_client import SentClient
from app.messaging.repositories.conexion_whatsapp_repository import (
    ConexionWhatsappRepository,
)
from app.messaging.services.conexion_whatsapp_service import ConexionWhatsappService
from app.messaging.services.envio_mensaje_service import EnvioMensajeService
from app.messaging.services.plantilla_otp_plataforma_service import (
    PlantillaOtpPlataformaService,
)
from app.templates.dependencies import get_templates_service
from app.templates.services.templates_service import TemplatesService


async def get_meta_client() -> AsyncGenerator[MetaClient]:
    cliente = MetaClient()
    try:
        yield cliente
    finally:
        await cliente.cerrar()


MetaClientDep = Annotated[MetaClient, Depends(get_meta_client)]


async def get_sent_client() -> AsyncGenerator[SentClient]:
    cliente = SentClient()
    try:
        yield cliente
    finally:
        await cliente.cerrar()


SentClientDep = Annotated[SentClient, Depends(get_sent_client)]


def get_conexion_whatsapp_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    meta_client: MetaClientDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
) -> ConexionWhatsappService:
    return ConexionWhatsappService(
        session,
        ConexionWhatsappRepository(session),
        meta_client,
        auth_service,
        plan_service,
    )


ConexionWhatsappServiceDep = Annotated[
    ConexionWhatsappService, Depends(get_conexion_whatsapp_service)
]


def get_envio_mensaje_service(
    conexion_service: ConexionWhatsappServiceDep,
    templates_service: Annotated[TemplatesService, Depends(get_templates_service)],
    contacts_service: Annotated[ContactsService, Depends(get_contacts_service)],
    meta_client: MetaClientDep,
    sent_client: SentClientDep,
) -> EnvioMensajeService:
    return EnvioMensajeService(
        conexion_service, templates_service, contacts_service, meta_client, sent_client
    )


EnvioMensajeServiceDep = Annotated[
    EnvioMensajeService, Depends(get_envio_mensaje_service)
]


def get_plantilla_otp_plataforma_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    meta_client: MetaClientDep,
) -> PlantillaOtpPlataformaService:
    return PlantillaOtpPlataformaService(session, meta_client)


PlantillaOtpPlataformaServiceDep = Annotated[
    PlantillaOtpPlataformaService, Depends(get_plantilla_otp_plataforma_service)
]
