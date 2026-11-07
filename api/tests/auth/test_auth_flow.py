"""Criterios de aceptación del Prompt 04: sesión real en Valkey (no solo el
JWT), MFA obligatoria, rotación de refresh token, y que ningún JSON de
respuesta lleve tokens.

El límite de un segundo usuario por plan (último criterio del prompt) no se
prueba aquí: depende de Plan (Prompt 03), que todavía no existe (ver
memoria `pulso-orden-de-fases`).
"""

import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"


def _email_de_prueba() -> str:
    return f"test-auth-{uuid.uuid4().hex[:12]}@acme.com"


@pytest.fixture(autouse=True)
async def _sin_rate_limit_entre_tests():
    # ASGITransport reporta siempre 127.0.0.1 como IP del cliente: sin esto,
    # el rate limit por IP de /auth se agota entre tests de este archivo.
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    yield


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c


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
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
    for clave in (
        f"login-fail:{email}",
        f"refresh:{usuario_id}",
        f"session:{usuario_id}",
        f"mfa_verified:{usuario_id}",
        f"otp-intentos:whatsapp:{usuario_id}",
    ):
        await valkey_client.delete(clave)


async def _registrar(cliente: AsyncClient, email: str) -> dict:
    respuesta = await cliente.post(
        "/auth/registro",
        json={
            "nombreOrganizacion": "Empresa de prueba",
            "email": email,
            "password": _PASSWORD,
        },
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def _extraer_codigo_otp(salida: str) -> str:
    coincidencia = re.search(r"codigo=(\d{6})", salida)
    assert coincidencia, f"no se encontró el código OTP en la salida: {salida!r}"
    return coincidencia.group(1)


async def test_ningun_json_de_respuesta_contiene_tokens(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        cuerpo = await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)
        assert "access_token" not in cuerpo
        assert "refresh_token" not in cuerpo
        assert "accessToken" not in cuerpo
        assert "refreshToken" not in cuerpo

        respuesta_login = await cliente.post(
            "/auth/login", json={"email": email, "password": _PASSWORD}
        )
        assert "access_token" not in respuesta_login.text
        assert "refresh_token" not in respuesta_login.text
    finally:
        await _limpiar(email, usuario_id)


def _usuario_id_desde_cookie(cliente: AsyncClient) -> int:
    from app.core.security.token_service import TokenService

    token = cliente.cookies.get("access_token")
    payload = TokenService().verificar_access_token(token)
    return int(payload["sub"])


async def test_sin_sesion_en_valkey_el_access_token_no_sirve(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        # El JWT sigue siendo válido (no expiró), pero borramos la sesión de
        # Valkey a mano: el token por sí solo no debe alcanzar.
        await valkey_client.delete(f"session:{usuario_id}")

        respuesta = await cliente.get("/auth/yo")
        assert respuesta.status_code == 401
    finally:
        await _limpiar(email, usuario_id)


async def test_sin_mfa_verificado_no_hay_acceso(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        respuesta = await cliente.get("/auth/yo")
        assert respuesta.status_code == 403
    finally:
        await _limpiar(email, usuario_id)


async def test_verificar_otp_habilita_el_acceso(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        await cliente.post("/auth/otp/enviar", json={"canal": "whatsapp"})
        codigo = _extraer_codigo_otp(capsys.readouterr().out)

        respuesta = await cliente.post(
            "/auth/otp/verificar", json={"codigo": codigo, "canal": "whatsapp"}
        )
        assert respuesta.status_code == 204

        respuesta_yo = await cliente.get("/auth/yo")
        assert respuesta_yo.status_code == 200
    finally:
        await _limpiar(email, usuario_id)


async def test_refresh_reutilizado_tras_rotacion_falla(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)
        refresh_viejo = cliente.cookies.get("refresh_token")

        primero = await cliente.post("/auth/refresh")
        assert primero.status_code == 200

        transporte = ASGITransport(app=app)
        async with AsyncClient(transport=transporte, base_url="https://test") as otro:
            otro.cookies.set("refresh_token", refresh_viejo)
            segundo = await otro.post("/auth/refresh")
            assert segundo.status_code == 401
    finally:
        await _limpiar(email, usuario_id)


async def test_login_nuevo_vuelve_a_exigir_mfa_aunque_quede_flag_anterior(
    cliente, capsys
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        await cliente.post("/auth/otp/enviar", json={"canal": "whatsapp"})
        codigo = _extraer_codigo_otp(capsys.readouterr().out)
        await cliente.post(
            "/auth/otp/verificar", json={"codigo": codigo, "canal": "whatsapp"}
        )
        assert (await cliente.get("/auth/yo")).status_code == 200

        # Nuevo login, sin cerrar sesión antes: debe volver a pedir MFA.
        await cliente.post("/auth/login", json={"email": email, "password": _PASSWORD})
        assert (await cliente.get("/auth/yo")).status_code == 403
    finally:
        await _limpiar(email, usuario_id)


async def test_logout_revoca_la_sesion_de_inmediato(cliente, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)
        await cliente.post("/auth/otp/enviar", json={"canal": "whatsapp"})
        codigo = _extraer_codigo_otp(capsys.readouterr().out)
        await cliente.post(
            "/auth/otp/verificar", json={"codigo": codigo, "canal": "whatsapp"}
        )
        assert (await cliente.get("/auth/yo")).status_code == 200

        respuesta_logout = await cliente.post("/auth/logout")
        assert respuesta_logout.status_code == 200

        assert (await cliente.get("/auth/yo")).status_code == 401
        assert (await cliente.post("/auth/refresh")).status_code == 401
    finally:
        await _limpiar(email, usuario_id)
