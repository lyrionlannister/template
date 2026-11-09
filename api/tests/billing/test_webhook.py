"""Criterio de aceptación de la Tarea 2: un checksum inválido se rechaza sin
persistir nada, y el mismo evento recibido dos veces no duplica fila ni se
reprocesa."""

import hashlib

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.billing.models.evento_pago_procesado_model import EventoPagoProcesado
from app.core.config.settings import get_settings
from app.core.database.session import async_session_factory
from main import app

_SECRETO_EVENTOS = "test_events_secret_webhook"


@pytest.fixture(autouse=True)
def _secreto_eventos(monkeypatch):
    monkeypatch.setenv("WOMPI_EVENTS_SECRET", _SECRETO_EVENTOS)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c


async def _limpiar(id_evento_externo: str) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(EventoPagoProcesado).where(
                EventoPagoProcesado.id_evento_externo == id_evento_externo
            )
        )
        await session.commit()


async def _contar(id_evento_externo: str) -> int:
    async with async_session_factory() as session:
        resultado = await session.execute(
            select(EventoPagoProcesado).where(
                EventoPagoProcesado.id_evento_externo == id_evento_externo
            )
        )
        return len(resultado.scalars().all())


def _payload_firmado(transaction_id: str, status: str, timestamp: int) -> dict:
    propiedades = ["transaction.id", "transaction.status"]
    data = {
        "transaction": {"id": transaction_id, "status": status, "reference": "REF-1"}
    }
    cadena = f"{transaction_id}{status}{timestamp}{_SECRETO_EVENTOS}"
    checksum = hashlib.sha256(cadena.encode()).hexdigest()
    return {
        "event": "transaction.updated",
        "data": data,
        "environment": "test",
        "signature": {"properties": propiedades, "checksum": checksum},
        "timestamp": timestamp,
    }


async def test_evento_con_checksum_invalido_se_rechaza_y_no_persiste(cliente):
    payload = _payload_firmado("tx-invalido", "APPROVED", 1700000001)
    payload["signature"]["checksum"] = "0" * 64

    respuesta = await cliente.post("/billing/webhooks/wompi", json=payload)

    assert respuesta.status_code == 401
    clave = "tx-invalido:APPROVED:1700000001"
    assert await _contar(clave) == 0


async def test_evento_duplicado_no_se_reprocesa(cliente):
    payload = _payload_firmado("tx-dup", "APPROVED", 1700000002)
    clave = "tx-dup:APPROVED:1700000002"
    try:
        primera = await cliente.post("/billing/webhooks/wompi", json=payload)
        segunda = await cliente.post("/billing/webhooks/wompi", json=payload)

        assert primera.status_code == 200
        assert segunda.status_code == 200
        assert await _contar(clave) == 1
    finally:
        await _limpiar(clave)
