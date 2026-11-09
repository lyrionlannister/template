"""Criterio de aceptación literal del prompt 07: un contacto nuevo que
cumple el filtro, creado después de armar ambas audiencias, lo refleja la
dinámica y no lo refleja la estática. Más autorización cruzada entre
tenants e inmutabilidad del filtro de una estática."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.audiences.enums.audiences_enums import TipoAudiencia
from app.audiences.exceptions import (
    AudienciaEstaticaInmutableError,
    AudienciaNoEncontradaError,
)
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


def _filtro_ciudad(valor: str) -> FiltroAudiencia:
    return FiltroAudiencia(
        and_=[Condicion(field="variables.ciudad", op="eq", value=valor)]
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


def _crear_audiencias_service(session) -> AudienciasService:
    return AudienciasService(
        session, AudienciaRepository(session), _crear_contacts_service(session)
    )


async def test_dinamica_refleja_contacto_nuevo_y_estatica_no() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000101", {"ciudad": "CDMX"})
    filtro = _filtro_ciudad("CDMX")

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_audiencias_service(session)
            dinamica = await servicio.crear(
                tenant_id, "Dinamica CDMX", TipoAudiencia.dinamica, filtro
            )
            estatica = await servicio.crear(
                tenant_id, "Estatica CDMX", TipoAudiencia.estatica, filtro
            )
            assert await servicio.contar(dinamica) == 1
            assert await servicio.contar(estatica) == 1

    # Contacto nuevo que cumple el filtro, creado DESPUÉS de ambas audiencias.
    await _crear_contacto(tenant_id, "+573000000102", {"ciudad": "CDMX"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_audiencias_service(session)
            dinamica = await servicio.obtener(dinamica.public_id)
            estatica = await servicio.obtener(estatica.public_id)
            assert await servicio.contar(dinamica) == 2
            assert await servicio.contar(estatica) == 1


async def test_actualizar_filtro_de_audiencia_estatica_se_rechaza() -> None:
    tenant_id = await _crear_tenant()
    filtro = _filtro_ciudad("CDMX")

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_audiencias_service(session)
            estatica = await servicio.crear(
                tenant_id, "Estatica", TipoAudiencia.estatica, filtro
            )
            with pytest.raises(AudienciaEstaticaInmutableError):
                await servicio.actualizar(
                    estatica.public_id, None, _filtro_ciudad("Bogota")
                )


async def test_actualizar_nombre_de_audiencia_estatica_si_funciona() -> None:
    tenant_id = await _crear_tenant()
    filtro = _filtro_ciudad("CDMX")

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_audiencias_service(session)
            estatica = await servicio.crear(
                tenant_id, "Nombre viejo", TipoAudiencia.estatica, filtro
            )
            actualizada = await servicio.actualizar(
                estatica.public_id, "Nombre nuevo", None
            )
    assert actualizada.nombre == "Nombre nuevo"


async def test_audiencia_de_un_tenant_no_es_alcanzable_desde_otro() -> None:
    tenant_a = await _crear_tenant()
    tenant_b = await _crear_tenant()
    filtro = _filtro_ciudad("CDMX")

    async with async_session_factory() as session:
        with set_current_tenant(tenant_a):
            servicio = _crear_audiencias_service(session)
            audiencia = await servicio.crear(
                tenant_a, "De A", TipoAudiencia.dinamica, filtro
            )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_b):
            servicio = _crear_audiencias_service(session)
            with pytest.raises(AudienciaNoEncontradaError):
                await servicio.obtener(audiencia.public_id)


async def test_duplicar_crea_audiencia_nueva_con_el_mismo_filtro() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000103", {"ciudad": "CDMX"})
    filtro = _filtro_ciudad("CDMX")

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_audiencias_service(session)
            original = await servicio.crear(
                tenant_id, "Original", TipoAudiencia.dinamica, filtro
            )
            copia = await servicio.duplicar(original.public_id, TipoAudiencia.estatica)

    assert copia.public_id != original.public_id
    assert copia.tipo == TipoAudiencia.estatica
    assert copia.filtro == original.filtro


async def test_campos_disponibles_incluye_base_y_variables_del_tenant() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000104", {"ciudad": "CDMX", "saldo": "1"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_audiencias_service(session)
            campos = await servicio.campos_disponibles()

    nombres = {campo["field"] for campo in campos}
    assert {"telefono", "creado_en", "variables.ciudad", "variables.saldo"} <= nombres
