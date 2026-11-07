"""Tests de `ContactsService.confirmar_importacion`: el `preview_id` de
otro tenant o uno expirado se rechazan igual (la clave de Valkey está
namespaceada por tenant), confirmar crea la `ImportacionContacto` y borra
la clave, y confirmar dos veces el mismo `preview_id` falla la segunda
porque la clave ya no existe."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.auth.dependencies import get_auth_service
from app.auth.enums.auth_enums import EstadoTenant
from app.auth.models.tenant_model import Tenant
from app.contacts.exceptions import (
    ColumnaTelefonoInvalidaError,
    PrevisualizacionNoEncontradaError,
)
from app.contacts.repositories.contacto_repository import ContactoRepository
from app.contacts.repositories.importacion_contacto_repository import (
    ImportacionContactoRepository,
)
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client


async def _crear_plan(limite_filas: int = 10) -> int:
    async with async_session_factory() as session:
        plan = Plan(
            nombre=f"plan-prueba-{uuid.uuid4().hex[:8]}",
            precio_mensual_cop=100_000,
            limite_filas_importacion=limite_filas,
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


def _crear_service(session: AsyncSession) -> ContactsService:
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
    )


async def _cachear_previsualizacion(tenant_id: int, preview_id: str) -> None:
    import json

    clave = f"importacion:preview:{tenant_id}:{preview_id}"
    await valkey_client.set(
        clave,
        json.dumps(
            {
                "nombre_archivo": "contactos.csv",
                "formato": "csv",
                "columnas": ["telefono", "nombre"],
                "filas": [{"telefono": "+573001112233", "nombre": "Ana"}],
            }
        ),
        ex=1800,
    )


async def test_confirmar_crea_importacion_y_borra_la_clave_de_valkey() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    preview_id = uuid.uuid4().hex
    await _cachear_previsualizacion(tenant_id, preview_id)

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        importacion = await servicio.confirmar_importacion(
            tenant_id,
            preview_id,
            columna_telefono="telefono",
            mapeo_variables={"nombre": "nombre"},
            background_tasks=BackgroundTasks(),
        )

    assert importacion.tenant_id == tenant_id
    assert importacion.nombre_archivo == "contactos.csv"
    assert importacion.total_filas == 1
    assert importacion.columna_telefono == "telefono"

    clave = f"importacion:preview:{tenant_id}:{preview_id}"
    assert await valkey_client.get(clave) is None


async def test_confirmar_dos_veces_el_mismo_preview_id_falla_la_segunda() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    preview_id = uuid.uuid4().hex
    await _cachear_previsualizacion(tenant_id, preview_id)

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        await servicio.confirmar_importacion(
            tenant_id,
            preview_id,
            columna_telefono="telefono",
            mapeo_variables={},
            background_tasks=BackgroundTasks(),
        )

        with pytest.raises(PrevisualizacionNoEncontradaError):
            await servicio.confirmar_importacion(
                tenant_id,
                preview_id,
                columna_telefono="telefono",
                mapeo_variables={},
                background_tasks=BackgroundTasks(),
            )


async def test_confirmar_con_preview_id_de_otro_tenant_falla() -> None:
    plan_id = await _crear_plan()
    tenant_id_dueno = await _crear_tenant(plan_id)
    tenant_id_atacante = await _crear_tenant(plan_id)
    preview_id = uuid.uuid4().hex
    await _cachear_previsualizacion(tenant_id_dueno, preview_id)

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with pytest.raises(PrevisualizacionNoEncontradaError):
            await servicio.confirmar_importacion(
                tenant_id_atacante,
                preview_id,
                columna_telefono="telefono",
                mapeo_variables={},
                background_tasks=BackgroundTasks(),
            )

    # La previsualización del dueño real sigue intacta: el intento del
    # atacante no la tocó.
    clave_dueno = f"importacion:preview:{tenant_id_dueno}:{preview_id}"
    assert await valkey_client.get(clave_dueno) is not None
    await valkey_client.delete(clave_dueno)


async def test_confirmar_con_preview_id_expirado_da_error_claro() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    preview_id = uuid.uuid4().hex
    # Nunca se cachea -- simula una previsualización cuyo TTL de 30 min ya
    # venció en Valkey: la clave sencillamente no existe.

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with pytest.raises(PrevisualizacionNoEncontradaError):
            await servicio.confirmar_importacion(
                tenant_id,
                preview_id,
                columna_telefono="telefono",
                mapeo_variables={},
                background_tasks=BackgroundTasks(),
            )


async def test_confirmar_rechaza_columna_telefono_que_no_existe() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    preview_id = uuid.uuid4().hex
    await _cachear_previsualizacion(tenant_id, preview_id)

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with pytest.raises(ColumnaTelefonoInvalidaError):
            await servicio.confirmar_importacion(
                tenant_id,
                preview_id,
                columna_telefono="columna_que_no_existe",
                mapeo_variables={},
                background_tasks=BackgroundTasks(),
            )
