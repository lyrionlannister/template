"""Smoke test de cableado HTTP y el criterio de aceptación "ninguna
plantilla puede cambiar de canal después de creada" probado end-to-end por
la API real (no solo por la firma del método)."""

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
    return f"test-templates-{uuid.uuid4().hex[:12]}@acme.com"


@pytest.fixture(autouse=True)
async def _sin_rate_limit_entre_tests():
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    yield


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c


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
            "nombreOrganizacion": "Empresa de prueba templates",
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


async def test_crear_plantilla_y_el_canal_no_cambia_con_patch(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta_crear = await cliente.post(
            "/templates",
            json={
                "nombre": "Saludo",
                "canal": "sms",
                "contenido": "Hola.",
                "nombrePlantillaSent": "plantilla_aprobada_sent",
            },
        )
        assert respuesta_crear.status_code == 201
        cuerpo = respuesta_crear.json()
        assert cuerpo["canal"] == "sms"
        public_id = cuerpo["publicId"]

        respuesta_patch = await cliente.patch(
            f"/templates/{public_id}", json={"canal": "whatsapp", "nombre": "Saludo v2"}
        )
        assert respuesta_patch.status_code == 200
        cuerpo_patch = respuesta_patch.json()
        assert cuerpo_patch["canal"] == "sms"
        assert cuerpo_patch["nombre"] == "Saludo v2"

        respuesta_whatsapp_sin_categoria = await cliente.post(
            "/templates",
            json={"nombre": "WA", "canal": "whatsapp", "contenido": "Hola."},
        )
        assert respuesta_whatsapp_sin_categoria.status_code == 422

        respuesta_borrar = await cliente.delete(f"/templates/{public_id}")
        assert respuesta_borrar.status_code == 204
    finally:
        await _limpiar(email, usuario_id)
