"""Tests de la política de conflicto de variables: todo conflicto real se
registra en `ConflictoVariableContacto` sin importar la política activa,
`no_pisar_marcar_advertencia` no sobrescribe y suma a
`filas_con_advertencia`, y `revertir_conflicto` restaura el valor anterior
una sola vez."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.auth.dependencies import get_auth_service
from app.auth.enums.auth_enums import EstadoTenant, RolUsuario
from app.auth.exceptions import PermisoInsuficienteError
from app.auth.models.tenant_model import Tenant
from app.auth.schemas.sesion_schema import SesionUsuario
from app.contacts.enums.contacts_enums import (
    EstadoImportacion,
    FormatoArchivoImportacion,
    PoliticaConflictoVariables,
)
from app.contacts.exceptions import (
    ConflictoNoEncontradoError,
    ConflictoYaRevertidoError,
)
from app.contacts.models.conflicto_variable_model import ConflictoVariableContacto
from app.contacts.models.contacto_model import Contacto
from app.contacts.models.importacion_contacto_model import ImportacionContacto
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
from app.contacts.services.contacts_service import (
    ContactsService,
    procesar_importacion_en_segundo_plano,
)
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant


async def _crear_plan() -> int:
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
        return plan.id


async def _crear_tenant(plan_id: int) -> int:
    async with async_session_factory() as session:
        tenant = Tenant(
            nombre=f"tenant-prueba-{uuid.uuid4().hex[:8]}",
            estado=EstadoTenant.activo,
            trial_fin=datetime.now(UTC) + timedelta(days=14),
            plan_id=plan_id,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        return tenant.id


async def _crear_importacion(tenant_id: int) -> int:
    async with async_session_factory() as session:
        importacion = ImportacionContacto(
            tenant_id=tenant_id,
            nombre_archivo="contactos.csv",
            formato=FormatoArchivoImportacion.csv,
            estado=EstadoImportacion.pendiente,
            columna_telefono="telefono",
            mapeo_variables={"nombre": "nombre"},
            total_filas=1,
        )
        session.add(importacion)
        await session.commit()
        await session.refresh(importacion)
        return importacion.id


def _crear_service(session) -> ContactsService:
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


async def _crear_contacto_con_variable(
    tenant_id: int, telefono: str, variables: dict[str, str]
) -> int:
    async with async_session_factory() as session:
        contacto = Contacto(tenant_id=tenant_id, telefono=telefono, variables=variables)
        session.add(contacto)
        await session.commit()
        await session.refresh(contacto)
        return contacto.id


async def test_conflicto_se_registra_con_politica_ultimo_gana_por_defecto() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    await _crear_contacto_con_variable(tenant_id, "+573001112233", {"nombre": "Ana"})
    importacion_id = await _crear_importacion(tenant_id)

    await procesar_importacion_en_segundo_plano(
        tenant_id,
        importacion_id,
        [{"telefono": "+573001112233", "nombre": "Andrea"}],
        "telefono",
        {"nombre": "nombre"},
    )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacto = (
                (
                    await session.execute(
                        select(Contacto).where(
                            Contacto.tenant_id == tenant_id,
                            Contacto.telefono == "+573001112233",
                        )
                    )
                )
                .scalars()
                .one()
            )
            conflicto = (
                (
                    await session.execute(
                        select(ConflictoVariableContacto).where(
                            ConflictoVariableContacto.importacion_id == importacion_id
                        )
                    )
                )
                .scalars()
                .one()
            )
            importacion = await session.get(ImportacionContacto, importacion_id)

    assert contacto.variables == {"nombre": "Andrea"}
    assert conflicto.clave == "nombre"
    assert conflicto.valor_anterior == "Ana"
    assert conflicto.valor_nuevo == "Andrea"
    assert conflicto.revertido_en is None
    assert importacion.filas_con_advertencia == 1


async def test_politica_no_pisar_marcar_advertencia_no_sobrescribe() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    await _crear_contacto_con_variable(tenant_id, "+573001112233", {"nombre": "Ana"})

    sesion_admin = SesionUsuario(
        usuario_id=1,
        tenant_id=tenant_id,
        email="admin@acme.com",
        rol=RolUsuario.administrador,
        mfa_habilitado=False,
    )
    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with set_current_tenant(tenant_id):
            await servicio.actualizar_politica_conflicto(
                sesion_admin, PoliticaConflictoVariables.no_pisar_marcar_advertencia
            )

    importacion_id = await _crear_importacion(tenant_id)
    await procesar_importacion_en_segundo_plano(
        tenant_id,
        importacion_id,
        [{"telefono": "+573001112233", "nombre": "Andrea"}],
        "telefono",
        {"nombre": "nombre"},
    )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            contacto = (
                (
                    await session.execute(
                        select(Contacto).where(
                            Contacto.tenant_id == tenant_id,
                            Contacto.telefono == "+573001112233",
                        )
                    )
                )
                .scalars()
                .one()
            )
            importacion = await session.get(ImportacionContacto, importacion_id)

    assert contacto.variables == {"nombre": "Ana"}
    assert importacion.filas_con_advertencia == 1
    assert importacion.filas_aceptadas == 1


async def test_actualizar_politica_conflicto_sin_rol_administrador_falla() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    sesion_miembro = SesionUsuario(
        usuario_id=2,
        tenant_id=tenant_id,
        email="miembro@acme.com",
        rol=RolUsuario.miembro,
        mfa_habilitado=False,
    )

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with set_current_tenant(tenant_id), pytest.raises(PermisoInsuficienteError):
            await servicio.actualizar_politica_conflicto(
                sesion_miembro, PoliticaConflictoVariables.ultimo_gana
            )


async def test_obtener_politica_conflicto_default_es_ultimo_gana() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with set_current_tenant(tenant_id):
            politica = await servicio.obtener_politica_conflicto()

    assert politica == PoliticaConflictoVariables.ultimo_gana


async def test_revertir_conflicto_restaura_el_valor_anterior_una_sola_vez() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    await _crear_contacto_con_variable(tenant_id, "+573001112233", {"nombre": "Ana"})
    importacion_id = await _crear_importacion(tenant_id)
    await procesar_importacion_en_segundo_plano(
        tenant_id,
        importacion_id,
        [{"telefono": "+573001112233", "nombre": "Andrea"}],
        "telefono",
        {"nombre": "nombre"},
    )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            conflicto = (
                (
                    await session.execute(
                        select(ConflictoVariableContacto).where(
                            ConflictoVariableContacto.importacion_id == importacion_id
                        )
                    )
                )
                .scalars()
                .one()
            )
            conflicto_public_id = conflicto.public_id

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with set_current_tenant(tenant_id):
            contacto = await servicio.revertir_conflicto(conflicto_public_id)

    assert contacto.variables == {"nombre": "Ana"}

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with set_current_tenant(tenant_id), pytest.raises(ConflictoYaRevertidoError):
            await servicio.revertir_conflicto(conflicto_public_id)


async def test_revertir_conflicto_inexistente_falla() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with set_current_tenant(tenant_id), pytest.raises(ConflictoNoEncontradoError):
            await servicio.revertir_conflicto(uuid.uuid4())
