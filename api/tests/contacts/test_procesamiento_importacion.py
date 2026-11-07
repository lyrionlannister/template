"""Tests de `procesar_importacion_en_segundo_plano`: reimportar el mismo
teléfono con variables distintas resulta en unión no destructiva, un
teléfono sin código de país se rechaza con el motivo exacto, y la
importación queda con sus contadores y su estado final correctos."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.app_platform.models.plan_model import Plan
from app.auth.enums.auth_enums import EstadoTenant
from app.auth.models.tenant_model import Tenant
from app.contacts.enums.contacts_enums import (
    EstadoImportacion,
    FormatoArchivoImportacion,
)
from app.contacts.models.contacto_model import Contacto
from app.contacts.models.contacto_rechazado_model import ContactoRechazado
from app.contacts.models.importacion_contacto_model import ImportacionContacto
from app.contacts.services.contacts_service import (
    fusionar_variables_no_destructivo,
    procesar_importacion_en_segundo_plano,
)
from app.contacts.utils.telefono_utils import MOTIVO_SIN_CODIGO_PAIS
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


async def _crear_importacion(tenant_id: int, total_filas: int) -> int:
    async with async_session_factory() as session:
        importacion = ImportacionContacto(
            tenant_id=tenant_id,
            nombre_archivo="contactos.csv",
            formato=FormatoArchivoImportacion.csv,
            estado=EstadoImportacion.pendiente,
            columna_telefono="telefono",
            mapeo_variables={"nombre": "nombre"},
            total_filas=total_filas,
        )
        session.add(importacion)
        await session.commit()
        await session.refresh(importacion)
        return importacion.id


def test_fusionar_variables_no_destructivo_no_pisa_con_vacio() -> None:
    existentes = {"nombre": "Ana", "ciudad": "Bogotá"}
    nuevas = {"nombre": "", "ciudad": "Medellín", "deuda": "100000"}
    resultado = fusionar_variables_no_destructivo(existentes, nuevas)
    assert resultado == {"nombre": "Ana", "ciudad": "Medellín", "deuda": "100000"}


async def test_reimportar_mismo_telefono_con_variables_distintas_fusiona() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)

    importacion_id_1 = await _crear_importacion(tenant_id, total_filas=1)
    await procesar_importacion_en_segundo_plano(
        tenant_id,
        importacion_id_1,
        [{"telefono": "+573001112233", "nombre": "Ana", "ciudad": "Bogotá"}],
        "telefono",
        {"nombre": "nombre", "ciudad": "ciudad"},
    )

    importacion_id_2 = await _crear_importacion(tenant_id, total_filas=1)
    await procesar_importacion_en_segundo_plano(
        tenant_id,
        importacion_id_2,
        [{"telefono": "+573001112233", "ciudad": "", "deuda": "100000"}],
        "telefono",
        {"ciudad": "ciudad", "deuda": "deuda"},
    )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            resultado = await session.execute(
                select(Contacto).where(
                    Contacto.tenant_id == tenant_id,
                    Contacto.telefono == "+573001112233",
                )
            )
            contacto = resultado.scalars().one()

    assert contacto.variables == {
        "nombre": "Ana",
        "ciudad": "Bogotá",
        "deuda": "100000",
    }


async def test_telefono_sin_codigo_de_pais_se_rechaza_con_motivo_exacto() -> None:
    plan_id = await _crear_plan()
    tenant_id = await _crear_tenant(plan_id)
    importacion_id = await _crear_importacion(tenant_id, total_filas=1)

    await procesar_importacion_en_segundo_plano(
        tenant_id,
        importacion_id,
        [{"telefono": "3001112233", "nombre": "Ana"}],
        "telefono",
        {"nombre": "nombre"},
    )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            importacion = await session.get(ImportacionContacto, importacion_id)
            resultado = await session.execute(
                select(ContactoRechazado).where(
                    ContactoRechazado.importacion_id == importacion_id
                )
            )
            rechazo = resultado.scalars().one()

    assert importacion.estado == EstadoImportacion.completada
    assert importacion.filas_aceptadas == 0
    assert importacion.filas_rechazadas == 1
    assert rechazo.motivo == MOTIVO_SIN_CODIGO_PAIS
    assert rechazo.fila_cruda == {"telefono": "3001112233", "nombre": "Ana"}
