"""Criterio de aceptación del Prompt 03: el pool de incluidos no se acumula
al cambiar de mes y un envío SMS nunca lo toca."""

import pytest

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.services.pool_incluidos_service import (
    UNIDADES_POR_MENSAJE_MARKETING,
    UNIDADES_POR_MENSAJE_UTILITY,
    PoolIncluidosService,
)
from app.core.valkey.client import valkey_client

_TENANT_DE_PRUEBA = 999_001


@pytest.fixture(autouse=True)
async def _limpiar_pool():
    yield
    async for clave in valkey_client.scan_iter(match=f"pool:{_TENANT_DE_PRUEBA}:*"):
        await valkey_client.delete(clave)


async def test_sms_nunca_toca_el_pool():
    servicio = PoolIncluidosService()
    unidades = await servicio.consumir(
        _TENANT_DE_PRUEBA, CanalMensajeria.sms, None, cantidad=5
    )
    assert unidades == 0
    assert await servicio.unidades_consumidas(_TENANT_DE_PRUEBA) == 0


async def test_marketing_consume_16_unidades_y_utility_1():
    servicio = PoolIncluidosService()
    await servicio.consumir(
        _TENANT_DE_PRUEBA, CanalMensajeria.whatsapp, CategoriaMensaje.marketing
    )
    await servicio.consumir(
        _TENANT_DE_PRUEBA, CanalMensajeria.whatsapp, CategoriaMensaje.utility
    )
    total = await servicio.unidades_consumidas(_TENANT_DE_PRUEBA)
    assert total == UNIDADES_POR_MENSAJE_MARKETING + UNIDADES_POR_MENSAJE_UTILITY


async def test_el_pool_no_se_acumula_entre_meses():
    servicio = PoolIncluidosService()
    await servicio.consumir(
        _TENANT_DE_PRUEBA, CanalMensajeria.whatsapp, CategoriaMensaje.marketing
    )
    assert await servicio.unidades_consumidas(_TENANT_DE_PRUEBA) == (
        UNIDADES_POR_MENSAJE_MARKETING
    )
    # Otro mes es, literalmente, otra clave: arranca en cero sin ningún job
    # de reinicio.
    assert await servicio.unidades_consumidas(_TENANT_DE_PRUEBA, mes="2099-01") == 0


async def test_disponibilidad_respeta_los_incluidos_del_plan():
    class _PlanFalso:
        mensajes_marketing_incluidos = 10

    servicio = PoolIncluidosService()
    disponibles_antes = await servicio.unidades_disponibles(
        _TENANT_DE_PRUEBA, _PlanFalso()
    )
    assert disponibles_antes == 10 * UNIDADES_POR_MENSAJE_MARKETING

    await servicio.consumir(
        _TENANT_DE_PRUEBA, CanalMensajeria.whatsapp, CategoriaMensaje.marketing
    )
    disponibles_despues = await servicio.unidades_disponibles(
        _TENANT_DE_PRUEBA, _PlanFalso()
    )
    assert disponibles_despues == disponibles_antes - UNIDADES_POR_MENSAJE_MARKETING
