"""Criterios de aceptación literales del prompt 08: render exitoso con
variables del JSON, render falla legible si falta una variable, WhatsApp
sin categoría se rechaza, y el canal no cambia después de creada."""

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
from app.audiences.enums.audiences_enums import TipoAudiencia
from app.audiences.repositories.audiencia_repository import AudienciaRepository
from app.audiences.services.audiencias_service import AudienciasService
from app.auth.dependencies import get_auth_service
from app.auth.enums.auth_enums import EstadoTenant
from app.auth.models.tenant_model import Tenant
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
from app.contacts.schemas.filtro_schema import Condicion, FiltroAudiencia
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant
from app.templates.exceptions import (
    CategoriaRequeridaError,
    NombrePlantillaMetaRequeridoError,
    VariableFaltanteEnRenderizadoError,
    VariableNoPermitidaError,
)
from app.templates.repositories.plantilla_repository import PlantillaRepository
from app.templates.services.templates_service import TemplatesService


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


def _crear_templates_service(session) -> TemplatesService:
    contacts_service = _crear_contacts_service(session)
    audiencias_service = AudienciasService(
        session, AudienciaRepository(session), contacts_service
    )
    return TemplatesService(
        session, PlantillaRepository(session), contacts_service, audiencias_service
    )


async def test_crear_extrae_variables_del_contenido_y_las_valida() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573001112201", {"saldo": "1000"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_templates_service(session)
            plantilla = await servicio.crear(
                tenant_id,
                "Recordatorio",
                CanalMensajeria.sms,
                "Hola {{telefono}}, tu saldo es {{saldo}}.",
                None,
                None,
            )
    assert plantilla.variables == ["telefono", "saldo"]


async def test_crear_rechaza_variable_que_no_existe_en_ningun_contacto() -> None:
    tenant_id = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_templates_service(session)
            with pytest.raises(VariableNoPermitidaError):
                await servicio.crear(
                    tenant_id,
                    "Invalida",
                    CanalMensajeria.sms,
                    "Hola {{columna_inventada}}.",
                    None,
                    None,
                )


async def test_whatsapp_sin_categoria_se_rechaza() -> None:
    tenant_id = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_templates_service(session)
            with pytest.raises(CategoriaRequeridaError):
                await servicio.crear(
                    tenant_id,
                    "WA sin categoria",
                    CanalMensajeria.whatsapp,
                    "Hola.",
                    None,
                    "plantilla_aprobada_meta",
                )


async def test_whatsapp_sin_nombre_plantilla_meta_se_rechaza() -> None:
    tenant_id = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_templates_service(session)
            with pytest.raises(NombrePlantillaMetaRequeridoError):
                await servicio.crear(
                    tenant_id,
                    "WA sin nombre meta",
                    CanalMensajeria.whatsapp,
                    "Hola.",
                    CategoriaMensaje.marketing,
                    None,
                )


async def test_whatsapp_con_categoria_y_nombre_meta_se_crea() -> None:
    tenant_id = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_templates_service(session)
            plantilla = await servicio.crear(
                tenant_id,
                "WA ok",
                CanalMensajeria.whatsapp,
                "Hola.",
                CategoriaMensaje.marketing,
                "plantilla_aprobada_meta",
            )
    assert plantilla.categoria == CategoriaMensaje.marketing
    assert plantilla.nombre_plantilla_meta == "plantilla_aprobada_meta"


async def test_actualizar_no_acepta_cambiar_canal_porque_el_metodo_no_lo_recibe() -> (
    None
):
    """`TemplatesService.actualizar` ni siquiera tiene parámetro `canal` --
    el canal es inmutable por diseño, no por una validación que se pueda
    saltar."""
    import inspect

    firma = inspect.signature(TemplatesService.actualizar)
    assert "canal" not in firma.parameters


async def test_renderizar_sustituye_variables_del_contacto_real() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573001112202", {"nombre": "Ana"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacts_service = _crear_contacts_service(session)
            contacto = await contacts_service.obtener_contacto(
                (
                    await contacts_service.contacto_repository.obtener_por_telefono(
                        "+573001112202"
                    )
                ).public_id
            )
            servicio = _crear_templates_service(session)
            plantilla = await servicio.crear(
                tenant_id,
                "Saludo",
                CanalMensajeria.sms,
                "Hola {{nombre}}, tu telefono es {{telefono}}.",
                None,
                None,
            )
            texto = await servicio.renderizar(plantilla.public_id, contacto.public_id)
    assert texto == "Hola Ana, tu telefono es +573001112202."


async def test_renderizar_falla_legible_si_el_contacto_no_trae_la_variable() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573001112203", {"nombre": "Ana"})
    await _crear_contacto(tenant_id, "+573001112204", {"otra_clave": "x"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacts_service = _crear_contacts_service(session)
            sin_nombre = (
                await contacts_service.contacto_repository.obtener_por_telefono(
                    "+573001112204"
                )
            )
            servicio = _crear_templates_service(session)
            plantilla = await servicio.crear(
                tenant_id,
                "Saludo",
                CanalMensajeria.sms,
                "Hola {{nombre}}.",
                None,
                None,
            )
            with pytest.raises(VariableFaltanteEnRenderizadoError):
                await servicio.renderizar(plantilla.public_id, sin_nombre.public_id)


async def test_verificar_audiencia_reporta_contactos_con_variable_faltante() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(
        tenant_id, "+573001112205", {"ciudad": "CDMX", "nombre": "Ana"}
    )
    await _crear_contacto(tenant_id, "+573001112206", {"ciudad": "CDMX"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_templates_service(session)
            plantilla = await servicio.crear(
                tenant_id,
                "Saludo",
                CanalMensajeria.sms,
                "Hola {{nombre}}.",
                None,
                None,
            )
            audiencias_service = servicio.audiencias_service
            filtro = FiltroAudiencia(
                and_=[Condicion(field="variables.ciudad", op="eq", value="CDMX")]
            )
            audiencia = await audiencias_service.crear(
                tenant_id, "CDMX", TipoAudiencia.dinamica, filtro
            )
            total, con_faltante = await servicio.verificar_audiencia(
                plantilla.public_id, audiencia.public_id
            )
    assert total == 2
    assert len(con_faltante) == 1
    assert con_faltante[0]["telefono"] == "+573001112206"


async def test_plantilla_de_un_tenant_no_es_alcanzable_desde_otro() -> None:
    tenant_a = await _crear_tenant()
    tenant_b = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_a):
            servicio = _crear_templates_service(session)
            plantilla = await servicio.crear(
                tenant_a, "De A", CanalMensajeria.sms, "Hola.", None, None
            )

    from app.templates.exceptions import PlantillaNoEncontradaError

    async with async_session_factory() as session:
        with set_current_tenant(tenant_b):
            servicio = _crear_templates_service(session)
            with pytest.raises(PlantillaNoEncontradaError):
                await servicio.obtener(plantilla.public_id)
