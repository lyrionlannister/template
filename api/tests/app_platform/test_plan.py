"""Criterios de aceptación del Prompt 03 sobre planes: la regla del 30% de
los incluidos, y que cambiar un precio en el panel se refleja sin tocar
código (se relee en vivo de la base, no de una constante)."""

from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.app_platform.exceptions import ReglaDeIncluidosVioladaError
from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import allow_system_scope

DATOS_PLAN_VALIDO = {
    "nombre": "Prueba Valido",
    "precio_mensual_cop": Decimal(149000),
    "limite_filas_importacion": 10_000,
    "mensajes_marketing_incluidos": 1_000,
    "precio_marketing_mensaje_cop": Decimal(90),
    "precio_utility_mensaje_cop": Decimal(15),
    "max_usuarios": 1,
    "max_whatsapp_numeros": 1,
}


def _servicio(session) -> PlanService:
    return PlanService(
        session,
        CostoCanalService(session),
        TipoCambioService(session),
        ParametroComercialService(session),
    )


@pytest.fixture(autouse=True)
async def _limpiar_planes_de_prueba():
    yield
    async with async_session_factory() as session:
        await session.execute(delete(Plan).where(Plan.nombre.like("Prueba%")))
        await session.commit()


async def test_esencial_real_pasa_la_regla_del_30_porciento():
    # Esencial, 1.000 incluidos a costo Meta vigente, cuesta menos del 30%
    # del neto tras Wompi (verificado a mano).
    async with async_session_factory() as session:
        with allow_system_scope():
            service = _servicio(session)
            await service._validar_regla_30_porciento(
                mensajes_incluidos=1_000, precio_mensual=Decimal(149000)
            )  # no debe lanzar


async def test_plan_con_incluidos_excesivos_se_rechaza():
    datos = dict(DATOS_PLAN_VALIDO)
    datos["nombre"] = "Prueba Excesivo"
    datos["mensajes_marketing_incluidos"] = 100_000  # muy por encima del 30%

    async with async_session_factory() as session:
        with allow_system_scope():
            service = _servicio(session)
            with pytest.raises(ReglaDeIncluidosVioladaError):
                await service.crear(datos)


async def test_cambiar_precio_se_lee_en_vivo_sin_tocar_codigo():
    async with async_session_factory() as session:
        with allow_system_scope():
            service = _servicio(session)
            datos = dict(DATOS_PLAN_VALIDO)
            datos["nombre"] = "Prueba Editable"
            plan = await service.crear(datos)

            actualizado = await service.actualizar(
                plan.public_id, {"precio_marketing_mensaje_cop": Decimal(120)}
            )
            releido = await service.obtener(plan.id)

    assert actualizado.precio_marketing_mensaje_cop == Decimal(120)
    assert releido.precio_marketing_mensaje_cop == Decimal(120)
