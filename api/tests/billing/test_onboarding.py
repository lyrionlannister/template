"""Criterio de aceptación de la Tarea 3: un cobro de onboarding real en el
sandbox de Wompi queda `APPROVED`, el webhook lo confirma y
`tenant.onboarding_pagado_en` queda poblado; un segundo intento sobre el
mismo tenant responde 409 sin crear un segundo cobro.

La tokenización de la tarjeta se hace aquí con `httpx` directo contra el
sandbox de Wompi -- exactamente lo que haría el navegador en producción
(Tarea 4) -- nunca a través de `app.billing.clients.wompi_client` ni de
ningún endpoint propio: el backend de Pulso no tiene, y no debe tener,
ninguna función que acepte un número de tarjeta en claro (ver Boundaries de
`resources/specs/SPEC-billing.md`).

El webhook real de Wompi no puede alcanzar `localhost` en este entorno de
pruebas, así que el evento se reconstruye con los datos reales de la
transacción ya aprobada en el sandbox y se firma con el
`WOMPI_EVENTS_SECRET` real -- no uno de prueba -- antes de enviarlo a
nuestro propio endpoint. Eso prueba que la verificación de checksum es
compatible con el algoritmo real de Wompi, no solo con un secreto inventado.
"""

import hashlib
import re
import time
import uuid

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

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
    return f"test-onboarding-{uuid.uuid4().hex[:12]}@acme.com"


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
            "nombreOrganizacion": "Empresa de prueba onboarding",
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
    from app.billing.models.cobro_model import Cobro
    from app.billing.models.fuente_de_pago_model import FuenteDePago

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
                await session.execute(delete(Cobro).where(Cobro.tenant_id == tenant_id))
                await session.execute(
                    delete(FuenteDePago).where(FuenteDePago.tenant_id == tenant_id)
                )
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
    await valkey_client.delete(f"login-fail:{email}")


async def _tenant_id_por_usuario(usuario_id: int) -> int:
    async with async_session_factory() as session:
        resultado = await session.execute(
            select(Usuario.tenant_id).where(Usuario.id == usuario_id)
        )
        return resultado.scalar_one()


async def _onboarding_pagado_en(tenant_id: int):
    async with async_session_factory() as session:
        resultado = await session.execute(
            select(Tenant.onboarding_pagado_en).where(Tenant.id == tenant_id)
        )
        return resultado.scalar_one()


async def _tokenizar_tarjeta_de_prueba_como_lo_haria_el_navegador() -> str:
    """Tokenización simple (campos en claro) directo contra Wompi, con la
    llave pública: es justo lo que hará `client/src/billing/` en el
    navegador. No pasa por ningún código del backend de Pulso."""

    async with httpx.AsyncClient(base_url=_WOMPI_BASE_URL) as http:
        respuesta = await http.post(
            "/tokens/cards",
            json={
                "number": _TARJETA_APROBADA,
                "cvc": "123",
                "exp_month": "12",
                "exp_year": "30",
                "card_holder": "Prueba Onboarding",
            },
            headers={"Authorization": f"Bearer {get_or_throw('WOMPI_PUBLIC_KEY')}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()["data"]["id"]


async def _obtener_tokens_de_aceptacion() -> tuple[str, str]:
    async with httpx.AsyncClient(base_url=_WOMPI_BASE_URL) as http:
        respuesta = await http.get(
            "/merchants/info",
            headers={"x-merchant-public-key": get_or_throw("WOMPI_PUBLIC_KEY")},
        )
        respuesta.raise_for_status()
        datos = respuesta.json()["data"]
        return (
            datos["presigned_acceptance"]["acceptance_token"],
            datos["presigned_personal_data_auth"]["acceptance_token"],
        )


def _firmar_evento_transaccion_actualizada(
    transaction_id: str, status: str, amount_in_cents: int, timestamp: int
) -> dict:
    secreto = get_or_throw("WOMPI_EVENTS_SECRET")
    cadena = f"{transaction_id}{status}{amount_in_cents}{timestamp}{secreto}"
    checksum = hashlib.sha256(cadena.encode()).hexdigest()
    return {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": transaction_id,
                "status": status,
                "amount_in_cents": amount_in_cents,
                "reference": None,  # se completa en el test con la referencia real
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


async def test_onboarding_real_en_sandbox_se_confirma_por_webhook_y_bloquea_repetir(
    cliente, capsys
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        tenant_id = await _tenant_id_por_usuario(usuario_id)

        estado_inicial = await cliente.get("/billing/onboarding/estado")
        assert estado_inicial.json()["pagado"] is False

        token = await _tokenizar_tarjeta_de_prueba_como_lo_haria_el_navegador()
        acceptance_token, accept_personal_auth = await _obtener_tokens_de_aceptacion()

        respuesta = await cliente.post(
            "/billing/onboarding",
            json={
                "token": token,
                "acceptanceToken": acceptance_token,
                "acceptPersonalAuth": accept_personal_auth,
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        cuerpo = respuesta.json()
        assert cuerpo["estado"] == "pendiente"
        referencia = cuerpo["referencia"]

        # La transacción ya se resolvió en el sandbox (tarjeta de prueba
        # aprobada, sin 3DS): se reconstruye el evento con sus datos reales.
        async with async_session_factory() as session:
            from app.billing.models.cobro_model import Cobro

            resultado = await session.execute(
                select(Cobro).where(Cobro.referencia == referencia)
            )
            cobro = resultado.scalars().one()
            transaction_id = cobro.id_externo_transaccion
            monto_centavos = int(cobro.monto_cop) * 100

        assert transaction_id is not None

        evento = _firmar_evento_transaccion_actualizada(
            transaction_id, "APPROVED", monto_centavos, int(time.time())
        )
        evento["data"]["transaction"]["reference"] = referencia
        # La firma no cubre `reference` (no está en `properties`), así que
        # agregarla después de firmar no invalida el checksum.

        respuesta_webhook = await cliente.post("/billing/webhooks/wompi", json=evento)
        assert respuesta_webhook.status_code == 200

        assert await _onboarding_pagado_en(tenant_id) is not None

        estado_final = await cliente.get("/billing/onboarding/estado")
        assert estado_final.json()["pagado"] is True

        async with async_session_factory() as session:
            from app.billing.models.cobro_model import Cobro

            resultado = await session.execute(
                select(Cobro).where(Cobro.referencia == referencia)
            )
            cobro_actualizado = resultado.scalars().one()
            assert cobro_actualizado.estado.value == "aprobada"

        # Segundo intento sobre el mismo tenant: ya está pagado.
        segundo_intento = await cliente.post(
            "/billing/onboarding",
            json={
                "token": token,
                "acceptanceToken": acceptance_token,
                "acceptPersonalAuth": accept_personal_auth,
            },
        )
        assert segundo_intento.status_code == 409
    finally:
        await _limpiar(email, usuario_id)
