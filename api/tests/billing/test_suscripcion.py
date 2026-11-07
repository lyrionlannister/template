"""Criterio de aceptación de la Tarea 6: una suscripción se cobra dos veces
seguidas en el sandbox real sin pedir 3DS la segunda vez (reusa la misma
fuente de pago preautorizada), y cada cobro se confirma solo por webhook."""

import asyncio
import hashlib
import re
import time
import uuid
from datetime import date

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.billing.models.cobro_model import Cobro
from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.billing.models.suscripcion_model import Suscripcion
from app.billing.services.suscripcion_service import SuscripcionService
from app.core.config.env_tools import get_or_throw
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"
_WOMPI_BASE_URL = "https://sandbox.wompi.co/v1"
_TARJETA_APROBADA = "4242424242424242"


def _email_de_prueba() -> str:
    return f"test-suscripcion-{uuid.uuid4().hex[:12]}@acme.com"


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
            "nombreOrganizacion": "Empresa de prueba suscripción",
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
                await session.execute(delete(Cobro).where(Cobro.tenant_id == tenant_id))
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
                "card_holder": "Prueba Suscripción",
            },
            headers={"Authorization": f"Bearer {get_or_throw('WOMPI_PUBLIC_KEY')}"},
        )
        respuesta.raise_for_status()
        return respuesta.json()["data"]["id"]


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


async def _forzar_suscripcion_vencida_hoy(tenant_id: int) -> None:
    async with async_session_factory() as session:
        resultado = await session.execute(
            select(Suscripcion).where(Suscripcion.tenant_id == tenant_id)
        )
        suscripcion = resultado.scalars().one()
        suscripcion.proxima_fecha_cobro = date.today()
        await session.commit()


async def test_suscripcion_se_cobra_dos_veces_sin_3ds_la_segunda(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        async with async_session_factory() as session:
            resultado = await session.execute(
                select(Usuario.tenant_id).where(Usuario.id == usuario_id)
            )
            tenant_id = resultado.scalar_one()

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

        estado_final = None
        for _ in range(20):
            estado_resp = await cliente.get(
                f"/billing/fuentes-de-pago/{public_id}/estado"
            )
            estado_final = estado_resp.json()["estado"]
            if estado_final != "pendiente":
                break
            await asyncio.sleep(1.5)
        assert estado_final == "disponible", estado_final

        suscripcion_estado = (await cliente.get("/billing/suscripcion/estado")).json()
        assert suscripcion_estado["existe"] is True
        assert suscripcion_estado["estado"] == "activa"

        from app.app_platform.services.costo_canal_service import CostoCanalService
        from app.app_platform.services.parametro_comercial_service import (
            ParametroComercialService,
        )
        from app.app_platform.services.plan_service import PlanService
        from app.app_platform.services.tipo_cambio_service import TipoCambioService
        from app.auth.dependencies import get_auth_service
        from app.billing.clients.wompi_client import WompiClient

        for numero_ciclo in (1, 2):
            await _forzar_suscripcion_vencida_hoy(tenant_id)

            async with async_session_factory() as session:
                parametro_comercial_service = ParametroComercialService(session)
                plan_service = PlanService(
                    session,
                    CostoCanalService(session),
                    TipoCambioService(session),
                    parametro_comercial_service,
                )
                auth_service = get_auth_service(
                    session, plan_service, parametro_comercial_service
                )
                wompi_client = WompiClient()
                try:
                    with set_current_tenant(tenant_id):
                        servicio = SuscripcionService(
                            session, wompi_client, auth_service, plan_service
                        )
                        procesadas = await servicio.cobrar_ciclo()
                finally:
                    await wompi_client.cerrar()
            assert procesadas == 1, f"ciclo {numero_ciclo}: {procesadas}"

            async with async_session_factory() as session:
                resultado = await session.execute(
                    select(Cobro)
                    .where(Cobro.tenant_id == tenant_id)
                    .order_by(Cobro.id.desc())
                )
                cobro = resultado.scalars().first()
            assert cobro is not None
            assert cobro.id_externo_transaccion is not None

            evento = _firmar_evento_transaccion_actualizada(
                cobro.id_externo_transaccion,
                "APPROVED",
                int(cobro.monto_cop) * 100,
                int(time.time()) + numero_ciclo,
            )
            evento["data"]["transaction"]["reference"] = cobro.referencia
            respuesta_webhook = await cliente.post(
                "/billing/webhooks/wompi", json=evento
            )
            assert respuesta_webhook.status_code == 200

            async with async_session_factory() as session:
                resultado = await session.execute(
                    select(Suscripcion).where(Suscripcion.tenant_id == tenant_id)
                )
                suscripcion = resultado.scalars().one()
            assert suscripcion.estado.value == "activa"
            assert suscripcion.intentos_fallidos_consecutivos == 0
            assert suscripcion.proxima_fecha_cobro > date.today()
    finally:
        await _limpiar(email, usuario_id)
