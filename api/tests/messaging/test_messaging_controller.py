"""Cableado HTTP del controller: cada excepción de dominio mapeada a su
código, happy path con los services reemplazados por un doble (primera vez
en el repo que se usa `dependency_overrides` -- a diferencia de Wompi,
Embedded Signup exige un popup real de OAuth en el navegador, no hay forma
de correrlo contra un sandbox desde un test de backend)."""

import re
import uuid
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.app_platform.exceptions import LimiteDePlanError
from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.contacts.exceptions import ContactoNoEncontradoError
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client
from app.messaging.dependencies import (
    get_conexion_whatsapp_service,
    get_envio_mensaje_service,
)
from app.messaging.exceptions import (
    ConexionWhatsappNoEncontradaError,
    NumeroYaConectadoError,
    VariableFaltanteParaEnvioError,
)
from app.messaging.services.dispatcher_service import CanalSinProveedorError
from app.templates.exceptions import PlantillaNoEncontradaError
from main import app

_PASSWORD = "Clave-Segura123"


def _email_de_prueba() -> str:
    return f"test-messaging-{uuid.uuid4().hex[:12]}@acme.com"


@pytest.fixture(autouse=True)
async def _sin_rate_limit_entre_tests():
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    yield


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c
    app.dependency_overrides.clear()


def _usuario_id_desde_cookie(cliente: AsyncClient) -> int:
    from app.core.security.token_service import TokenService

    token = cliente.cookies.get("access_token")
    payload = TokenService().verificar_access_token(token)
    return int(payload["sub"])


def _extraer_codigo_otp(salida: str) -> str:
    coincidencia = re.search(r"codigo=(\d{6})", salida)
    assert coincidencia, f"no se encontró el código OTP en la salida: {salida!r}"
    return coincidencia.group(1)


async def _registrar_y_verificar_mfa(cliente: AsyncClient, email: str, capsys) -> int:
    respuesta = await cliente.post(
        "/auth/registro",
        json={
            "nombreOrganizacion": "Empresa de prueba messaging",
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
                await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
    await valkey_client.delete(f"login-fail:{email}")


class _ConexionServiceFalso:
    def __init__(self, excepcion=None, resultado=None):
        self.excepcion = excepcion
        self.resultado = resultado

    async def conectar(self, *args, **kwargs):
        if self.excepcion:
            raise self.excepcion
        return self.resultado


class _EnvioServiceFalso:
    def __init__(self, excepcion=None, resultado=None):
        self.excepcion = excepcion
        self.resultado = resultado

    async def enviar_plantilla(self, *args, **kwargs):
        if self.excepcion:
            raise self.excepcion
        return self.resultado


class _ConexionFalsa:
    public_id = uuid4()
    waba_id = "waba-1"
    phone_number_id = "phone-1"
    numero_telefono = "+573001234567"
    creado_en = datetime.now(UTC)


@pytest.mark.parametrize(
    "excepcion,status_esperado",
    [
        (NumeroYaConectadoError("ya conectado"), 409),
        (LimiteDePlanError("limite alcanzado"), 409),
        (
            httpx.HTTPStatusError("boom", request=None, response=httpx.Response(400)),
            502,
        ),
    ],
)
async def test_conectar_whatsapp_mapea_cada_excepcion(
    cliente: AsyncClient, capsys, excepcion, status_esperado
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        app.dependency_overrides[get_conexion_whatsapp_service] = (
            lambda: _ConexionServiceFalso(excepcion=excepcion)
        )

        respuesta = await cliente.post(
            "/messaging/whatsapp/conectar",
            json={"code": "code-1", "wabaId": "waba-1", "phoneNumberId": "phone-1"},
        )
        assert respuesta.status_code == status_esperado
    finally:
        await _limpiar(email, usuario_id)


async def test_conectar_whatsapp_happy_path(cliente: AsyncClient, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        app.dependency_overrides[get_conexion_whatsapp_service] = (
            lambda: _ConexionServiceFalso(resultado=_ConexionFalsa())
        )

        respuesta = await cliente.post(
            "/messaging/whatsapp/conectar",
            json={"code": "code-1", "wabaId": "waba-1", "phoneNumberId": "phone-1"},
        )
        assert respuesta.status_code == 201
        assert respuesta.json()["numeroTelefono"] == "+573001234567"
    finally:
        await _limpiar(email, usuario_id)


@pytest.mark.parametrize(
    "excepcion,status_esperado",
    [
        (PlantillaNoEncontradaError("no existe"), 404),
        (ContactoNoEncontradoError("no existe"), 404),
        (VariableFaltanteParaEnvioError("falta variable"), 422),
        (ConexionWhatsappNoEncontradaError("sin conexion"), 409),
        (CanalSinProveedorError("sin proveedor"), 409),
        (
            httpx.HTTPStatusError("boom", request=None, response=httpx.Response(400)),
            502,
        ),
    ],
)
async def test_enviar_plantilla_mapea_cada_excepcion(
    cliente: AsyncClient, capsys, excepcion, status_esperado
):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        app.dependency_overrides[get_envio_mensaje_service] = (
            lambda: _EnvioServiceFalso(excepcion=excepcion)
        )

        respuesta = await cliente.post(
            "/messaging/plantillas/enviar",
            json={
                "plantillaPublicId": str(uuid4()),
                "contactoPublicId": str(uuid4()),
            },
        )
        assert respuesta.status_code == status_esperado
    finally:
        await _limpiar(email, usuario_id)


async def test_enviar_plantilla_happy_path(cliente: AsyncClient, capsys):
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)
        app.dependency_overrides[get_envio_mensaje_service] = (
            lambda: _EnvioServiceFalso(resultado={"messages": [{"id": "wamid.ok"}]})
        )

        respuesta = await cliente.post(
            "/messaging/plantillas/enviar",
            json={
                "plantillaPublicId": str(uuid4()),
                "contactoPublicId": str(uuid4()),
            },
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["messageId"] == "wamid.ok"
    finally:
        await _limpiar(email, usuario_id)
