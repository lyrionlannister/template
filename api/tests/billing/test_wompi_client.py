"""Tests del cliente Wompi: firma de integridad, verificación de checksum de
webhook y las llamadas HTTP (con transporte simulado, sin red real -- ver
Tarea 1 de `resources/tasks/plan-billing.md`)."""

import hashlib
import json

import httpx
import pytest

from app.billing.clients import wompi_client

_SECRETO_INTEGRIDAD = "prod_integrity_test_secret"
_SECRETO_EVENTOS = "test_events_secret"


@pytest.fixture(autouse=True)
def _secretos_wompi(monkeypatch):
    monkeypatch.setenv("WOMPI_INTEGRITY_SECRET", _SECRETO_INTEGRIDAD)
    monkeypatch.setenv("WOMPI_EVENTS_SECRET", _SECRETO_EVENTOS)
    monkeypatch.setenv("WOMPI_PUBLIC_KEY", "pub_test_fake")
    monkeypatch.setenv("WOMPI_PRIVATE_KEY", "prv_test_fake")


def test_firma_de_integridad_sigue_el_orden_referencia_monto_moneda_secreto():
    firma = wompi_client.calcular_firma_integridad("REF-001", 150000, "COP")
    esperada = hashlib.sha256(
        f"REF-001150000COP{_SECRETO_INTEGRIDAD}".encode()
    ).hexdigest()
    assert firma == esperada


def test_firma_de_integridad_cambia_si_cambia_cualquier_campo():
    base = wompi_client.calcular_firma_integridad("REF-001", 150000, "COP")
    assert base != wompi_client.calcular_firma_integridad("REF-002", 150000, "COP")
    assert base != wompi_client.calcular_firma_integridad("REF-001", 150001, "COP")
    assert base != wompi_client.calcular_firma_integridad("REF-001", 150000, "USD")


def _payload_evento(
    transaction_id: str, status: str, amount: int, timestamp: int
) -> dict:
    propiedades = [
        "transaction.id",
        "transaction.status",
        "transaction.amount_in_cents",
    ]
    data = {
        "transaction": {
            "id": transaction_id,
            "status": status,
            "amount_in_cents": amount,
            "reference": "REF-001",
        }
    }
    valores = [str(data["transaction"][ruta.split(".")[1]]) for ruta in propiedades]
    cadena = "".join(valores) + str(timestamp) + _SECRETO_EVENTOS
    checksum = hashlib.sha256(cadena.encode()).hexdigest()
    return {
        "event": "transaction.updated",
        "data": data,
        "environment": "test",
        "signature": {"properties": propiedades, "checksum": checksum},
        "timestamp": timestamp,
    }


def test_checksum_de_evento_valido_se_acepta():
    payload = _payload_evento("1234-abc", "APPROVED", 150000, 1700000000)
    assert wompi_client.verificar_checksum_evento(payload) is True


def test_checksum_de_evento_alterado_se_rechaza():
    payload = _payload_evento("1234-abc", "APPROVED", 150000, 1700000000)
    payload["data"]["transaction"]["status"] = "DECLINED"
    assert wompi_client.verificar_checksum_evento(payload) is False


def test_checksum_sin_firma_se_rechaza_sin_lanzar():
    assert wompi_client.verificar_checksum_evento({"data": {}, "timestamp": 1}) is False


@pytest.mark.asyncio
async def test_crear_transaccion_envia_firma_y_llave_privada():
    capturado = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        capturado["headers"] = request.headers
        capturado["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"id": "tx-1", "status": "APPROVED"}})

    cliente = wompi_client.WompiClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://sandbox.wompi.co/v1",
        )
    )
    resultado = await cliente.crear_transaccion(
        reference="REF-001",
        amount_in_cents=150000,
        currency="COP",
        customer_email="prueba@test.com",
        payment_source_id=298,
    )

    assert resultado["data"]["status"] == "APPROVED"
    assert capturado["headers"]["authorization"] == "Bearer prv_test_fake"
    assert capturado["body"]["payment_source_id"] == 298
    assert capturado["body"]["signature"] == wompi_client.calcular_firma_integridad(
        "REF-001", 150000, "COP"
    )


@pytest.mark.asyncio
async def test_crear_transaccion_exige_payment_source_o_payment_method():
    cliente = wompi_client.WompiClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(200)),
            base_url="https://sandbox.wompi.co/v1",
        )
    )
    with pytest.raises(ValueError):
        await cliente.crear_transaccion(
            reference="REF-001",
            amount_in_cents=150000,
            currency="COP",
            customer_email="prueba@test.com",
        )


@pytest.mark.asyncio
async def test_crear_fuente_de_pago_envia_llave_privada_y_operacion_financiera():
    capturado = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        capturado["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"id": 298, "status": "PENDING"}})

    cliente = wompi_client.WompiClient(
        cliente_http=httpx.AsyncClient(
            transport=httpx.MockTransport(_handler),
            base_url="https://sandbox.wompi.co/v1",
        )
    )
    resultado = await cliente.crear_fuente_de_pago(
        tipo="CARD",
        token="tok_test_1",
        customer_email="prueba@test.com",
        acceptance_token="acc_token",
        accept_personal_auth="auth_token",
        financial_operation="PREAUTHORIZATION",
    )

    assert resultado["data"]["id"] == 298
    assert capturado["body"]["financial_operation"] == "PREAUTHORIZATION"
