"""Recuperación de password (enlace por correo, vía Resend) y login con
Google (id_token verificado en backend). Ambos nuevos en esta tarea --
ningún correo ni verificación real sale a internet en los tests: se
reemplaza el cliente externo con un doble de prueba."""

import re
import uuid

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from sqlalchemy import delete

import app.auth.services.auth_service as auth_service_module
from app.auth.clients.google_client import GoogleTokenInvalidoError
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.core.database.session import async_session_factory
from app.core.security.token_service import TokenService
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"
_PASSWORD_NUEVA = "Otra-Clave-Segura456"


def _usuario_id_desde_cookie(cliente: AsyncClient) -> int:
    token = cliente.cookies.get("access_token")
    payload = TokenService().verificar_access_token(token)
    return int(payload["sub"])


async def _limpiar(usuario_id: int | None) -> None:
    if usuario_id is None:
        return
    async with async_session_factory() as session:
        resultado = await session.execute(
            delete(Usuario).where(Usuario.id == usuario_id).returning(Usuario.tenant_id)
        )
        tenant_id = resultado.scalar_one_or_none()
        if tenant_id is not None:
            await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()


def _email_de_prueba() -> str:
    return f"test-recuperacion-{uuid.uuid4().hex[:12]}@acme.com"


@pytest.fixture(autouse=True)
async def _sin_rate_limit_entre_tests():
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    await valkey_client.delete("ratelimit:recuperacion:127.0.0.1")
    yield


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c


async def _registrar(cliente: AsyncClient, email: str) -> None:
    respuesta = await cliente.post(
        "/auth/registro",
        json={"nombreOrganizacion": "Empresa de prueba", "email": email, "password": _PASSWORD},
    )
    assert respuesta.status_code == 201


def _extraer_token(html: str) -> str:
    coincidencia = re.search(r"token=([\w-]+)", html)
    assert coincidencia, f"no se encontró el token en el correo simulado: {html!r}"
    return coincidencia.group(1)


async def test_olvide_password_envia_correo_y_restablecer_cambia_la_password(
    cliente, monkeypatch
):
    email = _email_de_prueba()
    usuario_id = None
    correos_enviados = []

    async def _enviar_email_falso(**kwargs):
        correos_enviados.append(kwargs)

    monkeypatch.setattr(auth_service_module, "enviar_email", _enviar_email_falso)

    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        respuesta = await cliente.post("/auth/password/olvide", json={"email": email})
        assert respuesta.status_code == 204
        assert len(correos_enviados) == 1
        assert correos_enviados[0]["destinatario"] == email

        token = _extraer_token(correos_enviados[0]["html"])
        restablecer = await cliente.post(
            "/auth/password/restablecer",
            json={"token": token, "nuevaPassword": _PASSWORD_NUEVA},
        )
        assert restablecer.status_code == 204

        login_viejo = await cliente.post(
            "/auth/login", json={"email": email, "password": _PASSWORD}
        )
        assert login_viejo.status_code == 401

        login_nuevo = await cliente.post(
            "/auth/login", json={"email": email, "password": _PASSWORD_NUEVA}
        )
        assert login_nuevo.status_code == 200

        # El token es de un solo uso.
        reintento = await cliente.post(
            "/auth/password/restablecer",
            json={"token": token, "nuevaPassword": _PASSWORD_NUEVA},
        )
        assert reintento.status_code == 400
    finally:
        await _limpiar(usuario_id)


async def test_olvide_password_con_correo_inexistente_no_revela_nada(cliente, monkeypatch):
    llamadas = []

    async def _enviar_email_falso(**kwargs):
        llamadas.append(kwargs)

    monkeypatch.setattr(auth_service_module, "enviar_email", _enviar_email_falso)

    respuesta = await cliente.post(
        "/auth/password/olvide", json={"email": "no-existe@acme.com"}
    )
    assert respuesta.status_code == 204
    assert llamadas == []


async def test_olvide_password_cuando_el_envio_falla_da_502_sin_exponer_el_detalle(
    cliente, monkeypatch
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        async def _enviar_email_roto(**_kwargs):
            raise httpx.HTTPStatusError(
                "el dominio no esta verificado en el proveedor",
                request=httpx.Request("POST", "https://api.resend.com/emails"),
                response=httpx.Response(403),
            )

        monkeypatch.setattr(auth_service_module, "enviar_email", _enviar_email_roto)

        respuesta = await cliente.post("/auth/password/olvide", json={"email": email})
        assert respuesta.status_code == 502
        assert "resend" not in respuesta.text.lower()
        assert "verificad" not in respuesta.text.lower()
    finally:
        await _limpiar(usuario_id)


async def test_restablecer_password_con_token_invalido_da_400(cliente):
    respuesta = await cliente.post(
        "/auth/password/restablecer",
        json={"token": "token-que-no-existe", "nuevaPassword": _PASSWORD_NUEVA},
    )
    assert respuesta.status_code == 400


async def test_login_con_google_para_cuenta_existente_emite_sesion_pendiente_de_mfa(
    cliente, monkeypatch
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        await _registrar(cliente, email)
        usuario_id = _usuario_id_desde_cookie(cliente)

        async def _verificar_falso(_token):
            return email

        monkeypatch.setattr(auth_service_module, "verificar_id_token", _verificar_falso)

        respuesta = await cliente.post(
            "/auth/google", json={"idToken": "token-de-google-falso"}
        )
        assert respuesta.status_code == 200
        assert "accessToken" not in respuesta.text

        # Igual que un login normal: la sesión queda pendiente de MFA.
        assert (await cliente.get("/auth/yo")).status_code == 403
    finally:
        await _limpiar(usuario_id)


async def test_login_con_google_rechaza_correo_no_registrado(cliente, monkeypatch):
    async def _verificar_falso(_token):
        return "nadie-registrado@acme.com"

    monkeypatch.setattr(auth_service_module, "verificar_id_token", _verificar_falso)

    respuesta = await cliente.post("/auth/google", json={"idToken": "token-de-google-falso"})
    assert respuesta.status_code == 404


async def test_login_con_google_rechaza_token_invalido(cliente, monkeypatch):
    async def _verificar_falso(_token):
        raise GoogleTokenInvalidoError("Token de Google inválido o expirado.")

    monkeypatch.setattr(auth_service_module, "verificar_id_token", _verificar_falso)

    respuesta = await cliente.post("/auth/google", json={"idToken": "token-de-google-falso"})
    assert respuesta.status_code == 401
