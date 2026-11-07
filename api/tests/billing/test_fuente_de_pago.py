"""Criterio de aceptación de la Tarea 5: una fuente de pago con
preautorización queda `disponible` tras pasar 3DS real en el sandbox de
Wompi. El monto se calcula en el servidor desde el plan vigente del tenant
(Esencial, $149.000), nunca lo manda el cliente.
"""

import asyncio
import re
import uuid

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.core.config.env_tools import get_or_throw
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"
_WOMPI_BASE_URL = "https://sandbox.wompi.co/v1"
_TARJETA_APROBADA = "4242424242424242"


def _email_de_prueba() -> str:
    return f"test-fuente-pago-{uuid.uuid4().hex[:12]}@acme.com"


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
            "nombreOrganizacion": "Empresa de prueba fuente de pago",
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
    from app.billing.models.fuente_de_pago_model import FuenteDePago
    from app.billing.models.suscripcion_model import Suscripcion

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
                    delete(Suscripcion).where(Suscripcion.tenant_id == tenant_id)
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
                "card_holder": "Prueba Fuente De Pago",
            },
            headers={"Authorization": f"Bearer {get_or_throw('WOMPI_PUBLIC_KEY')}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()["data"]["id"]


async def test_fuente_de_pago_con_preautorizacion_queda_disponible_en_sandbox(
    cliente, capsys
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        tokens = (await cliente.get("/billing/tokens-aceptacion")).json()
        token = await _tokenizar_tarjeta_de_prueba_como_lo_haria_el_navegador()

        respuesta = await cliente.post(
            "/billing/fuentes-de-pago",
            json={
                "token": token,
                "acceptanceToken": tokens["acceptanceToken"],
                "acceptPersonalAuth": tokens["acceptPersonalAuth"],
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        public_id = respuesta.json()["publicId"]
        assert respuesta.json()["estado"] == "pendiente"

        estado_final = None
        for _ in range(20):
            estado_resp = await cliente.get(
                f"/billing/fuentes-de-pago/{public_id}/estado"
            )
            assert estado_resp.status_code == 200, estado_resp.text
            estado_final = estado_resp.json()["estado"]
            if estado_final != "pendiente":
                break
            await asyncio.sleep(1.5)

        assert (
            estado_final == "disponible"
        ), f"la fuente de pago no quedó disponible a tiempo: {estado_final!r}"
    finally:
        await _limpiar(email, usuario_id)
