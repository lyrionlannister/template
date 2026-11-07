"""Criterios de aceptación del Prompt 02: versionado del costo vigente,
acceso denegado a quien no tiene alcance de administrador del sistema, y
que el histórico no se puede actualizar ni borrar por la API.

Usa el canal SMS (sin fila sembrada por la migración, a diferencia de
WhatsApp) para no tocar la semilla real de costos al escribir/cerrar
vigencias en estos tests.
"""

from datetime import date
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.app_platform.enums.costo_canal_enums import CanalMensajeria
from app.app_platform.models.costo_canal_model import CostoCanal
from app.app_platform.services.costo_canal_service import (
    AccesoDeAdministradorRequeridoError,
    CostoCanalService,
)
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import allow_system_scope, set_current_tenant
from main import app


@pytest.fixture(autouse=True)
async def _limpiar_costos_sms():
    yield
    async with async_session_factory() as session:
        await session.execute(delete(CostoCanal).where(CostoCanal.canal == "sms"))
        await session.commit()


async def test_costo_vigente_en_fecha_pasada_no_cambia_al_registrar_uno_nuevo():
    async with async_session_factory() as session:
        with allow_system_scope():
            service = CostoCanalService(session)
            await service.registrar_costo(
                canal=CanalMensajeria.sms,
                categoria=None,
                proveedor="sent",
                costo_unitario=Decimal("50.0000"),
                moneda="COP",
                vigente_desde=date(2026, 1, 1),
                fuente="test",
            )
            await service.registrar_costo(
                canal=CanalMensajeria.sms,
                categoria=None,
                proveedor="sent",
                costo_unitario=Decimal("60.0000"),
                moneda="COP",
                vigente_desde=date(2026, 6, 1),
                fuente="test",
            )

            vigente_hoy = await service.costo_vigente(
                CanalMensajeria.sms, None, date(2026, 11, 1)
            )
            vigente_en_marzo = await service.costo_vigente(
                CanalMensajeria.sms, None, date(2026, 3, 1)
            )

    assert str(vigente_hoy.costo_unitario) == "60.0000"
    assert str(vigente_en_marzo.costo_unitario) == "50.0000"


async def test_registrar_costo_sin_alcance_de_sistema_se_rechaza():
    async with async_session_factory() as session:
        with set_current_tenant(1):
            service = CostoCanalService(session)
            with pytest.raises(AccesoDeAdministradorRequeridoError):
                await service.registrar_costo(
                    canal=CanalMensajeria.sms,
                    categoria=None,
                    proveedor="sent",
                    costo_unitario=Decimal("50.0000"),
                    moneda="COP",
                    vigente_desde=date(2026, 1, 1),
                    fuente="test",
                )


async def test_historico_sin_alcance_de_sistema_se_rechaza():
    async with async_session_factory() as session:
        with set_current_tenant(1):
            service = CostoCanalService(session)
            with pytest.raises(AccesoDeAdministradorRequeridoError):
                await service.historico(CanalMensajeria.whatsapp, None)


async def test_panel_del_sistema_rechaza_a_un_administrador_de_organizacion():
    # httpx.AsyncClient con ASGITransport, no el TestClient sincrono: este
    # corre la app en el mismo loop de asyncio que el test (el engine es un
    # singleton atado a un loop); el TestClient sincrono usa un hilo con su
    # propio loop y rompe la conexion de Postgres ("attached to a different
    # loop").
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test") as cliente:
        with set_current_tenant(1):
            respuesta = await cliente.get(
                "/app-platform/costos/historico", params={"canal": "whatsapp"}
            )
    assert respuesta.status_code == 403


async def test_panel_del_sistema_acepta_alcance_de_administrador():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test") as cliente:
        with allow_system_scope():
            respuesta = await cliente.get(
                "/app-platform/costos/historico", params={"canal": "whatsapp"}
            )
    assert respuesta.status_code == 200


def test_el_historico_no_expone_actualizar_ni_borrar_por_api():
    metodos = {
        route.path: route.methods
        for route in app.routes
        if getattr(route, "path", "").startswith("/app-platform/costos")
    }
    todos_los_metodos = {m for metodos_ruta in metodos.values() for m in metodos_ruta}
    assert "PUT" not in todos_los_metodos
    assert "PATCH" not in todos_los_metodos
    assert "DELETE" not in todos_los_metodos
