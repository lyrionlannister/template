"""Smoke test de cableado HTTP: sesión real (cookie, no mock), rutas
registradas, serialización en camelCase. La lógica de negocio ya está
probada en `test_audiencias_service.py`."""

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
    return f"test-audiencias-{uuid.uuid4().hex[:12]}@acme.com"


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
            "nombreOrganizacion": "Empresa de prueba audiencias",
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


async def test_crear_listar_obtener_y_eliminar_audiencia(
    cliente: AsyncClient, capsys
) -> None:
    email = _email_de_prueba()
    usuario_id = None
    try:
        usuario_id = await _registrar_y_verificar_mfa(cliente, email, capsys)

        respuesta_campos = await cliente.get("/audiences/campos")
        assert respuesta_campos.status_code == 200
        campos = respuesta_campos.json()["campos"]
        assert any(campo["field"] == "telefono" for campo in campos)

        cuerpo_filtro = {
            "and": [{"field": "telefono", "op": "contains", "value": "573"}]
        }
        respuesta_preview = await cliente.post(
            "/audiences/vista-previa", json={"filtro": cuerpo_filtro}
        )
        assert respuesta_preview.status_code == 200
        assert respuesta_preview.json()["conteo"] == 0

        respuesta_crear = await cliente.post(
            "/audiences",
            json={
                "nombre": "Mi audiencia",
                "tipo": "dinamica",
                "filtro": cuerpo_filtro,
            },
        )
        assert respuesta_crear.status_code == 201
        cuerpo = respuesta_crear.json()
        assert cuerpo["nombre"] == "Mi audiencia"
        assert cuerpo["tipo"] == "dinamica"
        assert cuerpo["conteo"] == 0
        public_id = cuerpo["publicId"]

        respuesta_listar = await cliente.get("/audiences")
        assert respuesta_listar.status_code == 200
        assert respuesta_listar.json()["total"] >= 1

        respuesta_detalle = await cliente.get(f"/audiences/{public_id}")
        assert respuesta_detalle.status_code == 200
        assert respuesta_detalle.json()["publicId"] == public_id

        respuesta_borrar = await cliente.delete(f"/audiences/{public_id}")
        assert respuesta_borrar.status_code == 204

        respuesta_404 = await cliente.get(f"/audiences/{public_id}")
        assert respuesta_404.status_code == 404
    finally:
        await _limpiar(email, usuario_id)
