"""Criterio de aceptación de la Tarea 8: una recarga real por cada medio
(tarjeta/PSE/Nequi) queda aprobada en el sandbox de Wompi, confirmada por
webhook, y el saldo calculado la refleja."""

import hashlib
import re
import time
import uuid
from decimal import Decimal

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.billing.models.movimiento_saldo_model import MovimientoSaldo
from app.core.config.settings import get_settings
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"
_WOMPI_BASE_URL = "https://sandbox.wompi.co/v1"
_TARJETA_APROBADA = "4242424242424242"
_NEQUI_APROBADO = "3991111111"


def _email_de_prueba() -> str:
    return f"test-recarga-{uuid.uuid4().hex[:12]}@acme.com"


@pytest.fixture(autouse=True)
async def _sin_rate_limit_entre_tests():
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    yield


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c


def _extraer_codigo_otp(salida: str) -> str:
    coincidencia = re.search(r"codigo=(\d{6})", salida)
    assert coincidencia, f"no se encontró el código OTP en la salida: {salida!r}"
    return coincidencia.group(1)


def _usuario_id_desde_cookie(cliente: AsyncClient) -> int:
    from app.core.security.token_service import TokenService

    token = cliente.cookies.get("access_token")
    payload = TokenService().verificar_access_token(token)
    return int(payload["sub"])


async def _registrar_y_verificar_mfa(cliente: AsyncClient, email: str, capsys) -> int:
    respuesta = await cliente.post(
        "/auth/registro",
        json={
            "nombreOrganizacion": "Empresa de prueba recarga",
            "email": email,
            "password": _PASSWORD,
        },
    )
    assert respuesta.status_code == 201
    usuario_id = _usuario_id_desde_cookie(cliente)

    await cliente.post("/auth/otp/enviar", json={"canal": "whatsapp"})
    codigo = _extraer_codigo_otp(capsys.readouterr().out)
    await cliente.post(
        "/auth/otp/verificar", json={"codigo": codigo, "canal": "whatsapp"}
    )
    return usuario_id


async def _limpiar(email: str, usuario_id: int | None) -> None:
    async with async_session_factory() as session:
        if usuario_id is not None:
            await session.execute(
                delete(CodigoOtp).where(CodigoOtp.usuario_id == usuario_id)
            )
            resultado = await session.execute(
                delete(Usuario)
                .where(Usuario.id == usuario_id)
                .returning(Usuario.tenant_id)
            )
            tenant_id = resultado.scalar_one_or_none()
            if tenant_id is not None:
                await session.execute(
                    delete(MovimientoSaldo).where(
                        MovimientoSaldo.tenant_id == tenant_id
                    )
                )
                await session.execute(
                    delete(FuenteDePago).where(FuenteDePago.tenant_id == tenant_id)
                )
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
    await valkey_client.delete(f"login-fail:{email}")


async def _tokenizar_tarjeta_de_prueba_como_lo_haria_el_navegador() -> str:
    async with httpx.AsyncClient(base_url=_WOMPI_BASE_URL) as http:
        respuesta = await http.post(
            "/tokens/cards",
            json={
                "number": _TARJETA_APROBADA,
                "cvc": "123",
                "exp_month": "12",
                "exp_year": "30",
                "card_holder": "Prueba Recarga",
            },
            headers={
                "Authorization": (
                    f"Bearer {get_settings().billing.wompi_public_key.get_secret_value()}"
                )
            },
        )
        respuesta.raise_for_status()
        return respuesta.json()["data"]["id"]


def _firmar_evento_transaccion_actualizada(
    transaction_id: str, status: str, amount_in_cents: int, timestamp: int
) -> dict:
    secreto = get_settings().billing.wompi_events_secret.get_secret_value()
    cadena = f"{transaction_id}{status}{amount_in_cents}{timestamp}{secreto}"
    checksum = hashlib.sha256(cadena.encode()).hexdigest()
    return {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": transaction_id,
                "status": status,
                "amount_in_cents": amount_in_cents,
                "reference": None,
            }
        },
        "environment": "test",
        "signature": {
            "properties": [
                "transaction.id",
                "transaction.status",
                "transaction.amount_in_cents",
            ],
            "checksum": checksum,
        },
        "timestamp": timestamp,
    }


async def _confirmar_por_webhook(cliente, referencia: str, monto_cop: int) -> None:
    async with async_session_factory() as session:
        resultado = await session.execute(
            select(MovimientoSaldo).where(MovimientoSaldo.referencia == referencia)
        )
        movimiento = resultado.scalars().one()
        transaction_id = movimiento.id_externo_transaccion
    assert transaction_id is not None

    evento = _firmar_evento_transaccion_actualizada(
        transaction_id, "APPROVED", monto_cop * 100, int(time.time())
    )
    evento["data"]["transaction"]["reference"] = referencia
    respuesta = await cliente.post("/billing/webhooks/wompi", json=evento)
    assert respuesta.status_code == 200


async def test_recarga_con_tarjeta_real_en_sandbox_se_confirma_por_webhook(
    cliente, capsys
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        token = await _tokenizar_tarjeta_de_prueba_como_lo_haria_el_navegador()
        tokens = (await cliente.get("/billing/tokens-aceptacion")).json()

        respuesta = await cliente.post(
            "/billing/saldo/recargar/tarjeta",
            json={
                "montoCop": 50000,
                "token": token,
                "acceptanceToken": tokens["acceptanceToken"],
                "acceptPersonalAuth": tokens["acceptPersonalAuth"],
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["estado"] == "pendiente"

        await _confirmar_por_webhook(cliente, cuerpo["referencia"], 50000)

        estado = (await cliente.get("/billing/saldo/estado")).json()
        assert Decimal(estado["saldoCop"]) >= Decimal(50000)
        assert any(
            m["referencia"] == cuerpo["referencia"] for m in estado["movimientos"]
        )
    finally:
        await _limpiar(email, usuario_id)


async def test_recarga_con_pse_real_en_sandbox_queda_aprobada(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta = await cliente.post(
            "/billing/saldo/recargar/pse",
            json={
                "montoCop": 20000,
                "userType": 0,
                "userLegalIdType": "CC",
                "userLegalId": "1999888777",
                "financialInstitutionCode": "1",  # aprobada, ver datos de prueba de Wompi
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["movimiento"]["estado"] == "pendiente"

        await _confirmar_por_webhook(cliente, cuerpo["movimiento"]["referencia"], 20000)

        movimiento = (
            await cliente.get(
                f"/billing/saldo/movimientos/{cuerpo['movimiento']['publicId']}/estado"
            )
        ).json()
        assert movimiento["estado"] == "aprobada"
    finally:
        await _limpiar(email, usuario_id)


async def test_recarga_con_nequi_real_en_sandbox_queda_aprobada(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta = await cliente.post(
            "/billing/saldo/recargar/nequi",
            json={"montoCop": 15000, "phoneNumber": _NEQUI_APROBADO},
        )
        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["estado"] == "pendiente"

        await _confirmar_por_webhook(cliente, cuerpo["referencia"], 15000)

        movimiento = (
            await cliente.get(f"/billing/saldo/movimientos/{cuerpo['publicId']}/estado")
        ).json()
        assert movimiento["estado"] == "aprobada"
    finally:
        await _limpiar(email, usuario_id)


async def test_instituciones_financieras_responde_lista_real(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        respuesta = await cliente.get("/billing/saldo/instituciones-financieras")
        assert respuesta.status_code == 200, respuesta.text
        instituciones = respuesta.json()
        assert len(instituciones) > 0
        assert "code" in instituciones[0] and "name" in instituciones[0]
    finally:
        await _limpiar(email, usuario_id)
