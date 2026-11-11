"""`EnvioMensajeService` contra la base real: los parámetros de Meta deben
quedar en el mismo orden en que las variables aparecen en el contenido de
la plantilla (orden posicional {{1}}, {{2}}...), y un contacto sin alguna
variable falla legible antes de llamar a Meta."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.audiences.repositories.audiencia_repository import AudienciaRepository
from app.audiences.services.audiencias_service import AudienciasService
from app.auth.dependencies import get_auth_service
from app.auth.enums.auth_enums import EstadoTenant, RolUsuario
from app.auth.models.tenant_model import Tenant
from app.auth.schemas.sesion_schema import SesionUsuario
from app.contacts.models.contacto_model import Contacto
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
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant
from app.messaging.exceptions import VariableFaltanteParaEnvioError
from app.messaging.repositories.conexion_whatsapp_repository import (
    ConexionWhatsappRepository,
)
from app.messaging.services.conexion_whatsapp_service import ConexionWhatsappService
from app.messaging.services.envio_mensaje_service import EnvioMensajeService
from app.templates.repositories.plantilla_repository import PlantillaRepository
from app.templates.services.templates_service import TemplatesService


class _MetaClientFalso:
    def __init__(self):
        self.enviados: list[dict] = []

    async def intercambiar_code_por_token(self, code: str) -> dict:
        return {"access_token": "tok-plano"}

    async def obtener_numero_telefono(self, phone_number_id, token_acceso) -> str:
        return "+573001234567"

    async def enviar_plantilla(self, **kwargs) -> dict:
        self.enviados.append(kwargs)
        return {"messages": [{"id": "wamid.falso-1"}]}


class _SentClientFalso:
    def __init__(self):
        self.enviados: list[dict] = []

    async def enviar_plantilla(self, **kwargs) -> dict:
        self.enviados.append(kwargs)
        return {"data": {"recipients": [{"message_id": "sent-falso-1"}]}}


async def _crear_tenant() -> int:
    async with async_session_factory() as session:
        plan = Plan(
            nombre=f"plan-prueba-{uuid.uuid4().hex[:8]}",
            precio_mensual_cop=100_000,
            limite_filas_importacion=1000,
            mensajes_marketing_incluidos=1000,
            precio_marketing_mensaje_cop=90,
            precio_utility_mensaje_cop=15,
            max_usuarios=1,
            max_whatsapp_numeros=1,
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        tenant = Tenant(
            nombre=f"tenant-prueba-{uuid.uuid4().hex[:8]}",
            estado=EstadoTenant.activo,
            trial_fin=datetime.now(UTC) + timedelta(days=14),
            plan_id=plan.id,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        return tenant.id


async def _crear_contacto(tenant_id: int, telefono: str, variables: dict) -> None:
    async with async_session_factory() as session:
        contacto = Contacto(tenant_id=tenant_id, telefono=telefono, variables=variables)
        session.add(contacto)
        await session.commit()


def _sesion_de(tenant_id: int) -> SesionUsuario:
    return SesionUsuario(
        usuario_id=1,
        tenant_id=tenant_id,
        email="prueba@test.com",
        rol=RolUsuario.administrador,
        mfa_habilitado=False,
    )


def _crear_contacts_service(session) -> ContactsService:
    parametro_comercial_service = ParametroComercialService(session)
    plan_service = PlanService(
        session,
        CostoCanalService(session),
        TipoCambioService(session),
        parametro_comercial_service,
    )
    auth_service = get_auth_service(session, plan_service, parametro_comercial_service)
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


def _crear_templates_service(session, contacts_service) -> TemplatesService:
    audiencias_service = AudienciasService(
        session, AudienciaRepository(session), contacts_service
    )
    return TemplatesService(
        session, PlantillaRepository(session), contacts_service, audiencias_service
    )


def _crear_envio_service(
    session, contacts_service, templates_service, meta_falso, sent_falso=None
):
    parametro_comercial_service = ParametroComercialService(session)
    plan_service = PlanService(
        session,
        CostoCanalService(session),
        TipoCambioService(session),
        parametro_comercial_service,
    )
    auth_service = get_auth_service(session, plan_service, parametro_comercial_service)
    conexion_service = ConexionWhatsappService(
        session,
        ConexionWhatsappRepository(session),
        meta_falso,
        auth_service,
        plan_service,
    )
    return conexion_service, EnvioMensajeService(
        conexion_service,
        templates_service,
        contacts_service,
        meta_falso,
        sent_falso or _SentClientFalso(),
    )


async def test_envia_los_parametros_posicionales_en_el_orden_del_contenido():
    tenant_id = await _crear_tenant()
    await _crear_contacto(
        tenant_id, "+573009990001", {"nombre": "Ana", "monto": "100000"}
    )
    meta_falso = _MetaClientFalso()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacts_service = _crear_contacts_service(session)
            templates_service = _crear_templates_service(session, contacts_service)
            conexion_service, envio_service = _crear_envio_service(
                session, contacts_service, templates_service, meta_falso
            )
            await conexion_service.conectar(
                _sesion_de(tenant_id),
                "code-1",
                "waba-1",
                f"phone-{uuid.uuid4().hex[:8]}",
            )
            plantilla = await templates_service.crear(
                tenant_id,
                "Pago recibido",
                CanalMensajeria.whatsapp,
                "Hola {{nombre}}, recibimos tu pago de {{monto}}.",
                CategoriaMensaje.utility,
                "pago_recibido_meta",
            )
            contacto = await contacts_service.obtener_contacto(
                (
                    await contacts_service.contacto_repository.obtener_por_telefono(
                        "+573009990001"
                    )
                ).public_id
            )
            await envio_service.enviar_plantilla(
                plantilla.public_id, contacto.public_id
            )

    assert len(meta_falso.enviados) == 1
    assert meta_falso.enviados[0]["parametros_posicionales"] == ["Ana", "100000"]
    assert meta_falso.enviados[0]["nombre_plantilla"] == "pago_recibido_meta"


async def test_contacto_sin_variable_falla_legible_antes_de_llamar_a_meta():
    tenant_id = await _crear_tenant()
    # "monto" debe existir como clave válida en la organización (en otro
    # contacto) para que la plantilla se pueda crear -- pero falta
    # justo en el contacto al que se le va a enviar.
    await _crear_contacto(tenant_id, "+573009990002", {"nombre": "Ana"})
    await _crear_contacto(tenant_id, "+573009990003", {"nombre": "Luis", "monto": "1"})
    meta_falso = _MetaClientFalso()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacts_service = _crear_contacts_service(session)
            templates_service = _crear_templates_service(session, contacts_service)
            conexion_service, envio_service = _crear_envio_service(
                session, contacts_service, templates_service, meta_falso
            )
            await conexion_service.conectar(
                _sesion_de(tenant_id),
                "code-1",
                "waba-1",
                f"phone-{uuid.uuid4().hex[:8]}",
            )
            plantilla = await templates_service.crear(
                tenant_id,
                "Pago recibido",
                CanalMensajeria.whatsapp,
                "Hola {{nombre}}, recibimos tu pago de {{monto}}.",
                CategoriaMensaje.utility,
                "pago_recibido_meta",
            )
            contacto = await contacts_service.obtener_contacto(
                (
                    await contacts_service.contacto_repository.obtener_por_telefono(
                        "+573009990002"
                    )
                ).public_id
            )
            with pytest.raises(VariableFaltanteParaEnvioError):
                await envio_service.enviar_plantilla(
                    plantilla.public_id, contacto.public_id
                )

    assert meta_falso.enviados == []


async def test_sms_envia_por_sent_con_parametros_nombrados():
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573009990004", {"nombre": "Ana"})
    meta_falso = _MetaClientFalso()
    sent_falso = _SentClientFalso()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacts_service = _crear_contacts_service(session)
            templates_service = _crear_templates_service(session, contacts_service)
            _, envio_service = _crear_envio_service(
                session, contacts_service, templates_service, meta_falso, sent_falso
            )
            plantilla = await templates_service.crear(
                tenant_id,
                "Recordatorio",
                CanalMensajeria.sms,
                "Hola {{nombre}}.",
                None,
                None,
                "plantilla_aprobada_sent",
            )
            contacto = await contacts_service.obtener_contacto(
                (
                    await contacts_service.contacto_repository.obtener_por_telefono(
                        "+573009990004"
                    )
                ).public_id
            )
            await envio_service.enviar_plantilla(
                plantilla.public_id, contacto.public_id
            )

    assert meta_falso.enviados == []
    assert len(sent_falso.enviados) == 1
    enviado = sent_falso.enviados[0]
    assert enviado["canal"] == CanalMensajeria.sms
    assert enviado["telefono_destino"] == "+573009990004"
    assert enviado["nombre_plantilla"] == "plantilla_aprobada_sent"
    assert enviado["parametros"] == {"nombre": "Ana"}
