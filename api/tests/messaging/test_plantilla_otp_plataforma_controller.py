"""Cableado HTTP: la ruta exige superadmin real, con los services
reemplazados por un doble (mismo patrón de `test_messaging_controller.py`)."""

import re
import uuid
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update

from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client
from app.messaging.dependencies import get_plantilla_otp_plataforma_service
from main import app

_PASSWORD = "Clave-Segura123"


def _email_de_prueba() -> str:
    return f"test-plantilla-otp-{uuid.uuid4().hex[:12]}@acme.com"


def _extraer_codigo_otp(salida: str) -> str:
    coincidencia = re.search(r"codigo=(\d{6})", salida)
    assert coincidencia, f"no se encontró el código OTP en la salida: {salida!r}"
    return coincidencia.group(1)


async def _registrar_y_verificar(cliente: AsyncClient, email: str, capsys, *, superadmin: bool):
    await valkey_client.delete("ratelimit:auth:127.0.0.1")
    respuesta = await cliente.post(
        "/auth/registro",
        json={"nombreOrganizacion": "Empresa de prueba", "email": email, "password": _PASSWORD},
    )
    assert respuesta.status_code == 201
    if superadmin:
        async with async_session_factory() as session:
            await session.execute(
                update(Usuario).where(Usuario.email == email).values(es_superadmin=True)
            )
            await session.commit()
        await cliente.post("/auth/login", json={"email": email, "password": _PASSWORD})
    await cliente.post("/auth/otp/enviar", json={"canal": "whatsapp"})
    codigo = _extraer_codigo_otp(capsys.readouterr().out)
    await cliente.post("/auth/otp/verificar", json={"codigo": codigo, "canal": "whatsapp"})


async def _limpiar(email: str):
    async with async_session_factory() as session:
        usuario = (
            await session.execute(select(Usuario).where(Usuario.email == email))
        ).scalar_one_or_none()
        if usuario is None:
            return
        tenant_id = usuario.tenant_id
        await session.execute(delete(CodigoOtp).where(CodigoOtp.usuario_id == usuario.id))
        await session.execute(delete(Usuario).where(Usuario.id == usuario.id))
        await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()


@pytest.fixture
async def cliente():
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="https://test") as c:
        yield c
    app.dependency_overrides.clear()


class _ServiceFalso:
    public_id = uuid4()
    nombre = "pulso_otp"
    idioma = "es"
    estado_meta = "PENDING"
    creado_en = datetime.now(UTC)

    async def crear(self, nombre, idioma):
        return self

    async def listar(self):
        return [self]

    async def sincronizar_estado(self, public_id):
        self.estado_meta = "APPROVED"
        return self


async def test_rechaza_a_un_administrador_de_organizacion(cliente: AsyncClient, capsys):
    email = _email_de_prueba()
    try:
        await _registrar_y_verificar(cliente, email, capsys, superadmin=False)
        respuesta = await cliente.get("/messaging/plataforma/plantilla-otp")
        assert respuesta.status_code == 403
    finally:
        await _limpiar(email)


async def test_superadmin_puede_crear_y_listar(cliente: AsyncClient, capsys):
    email = _email_de_prueba()
    app.dependency_overrides[get_plantilla_otp_plataforma_service] = lambda: _ServiceFalso()
    try:
        await _registrar_y_verificar(cliente, email, capsys, superadmin=True)
        respuesta = await cliente.post(
            "/messaging/plataforma/plantilla-otp", json={"nombre": "Pulso OTP", "idioma": "es"}
        )
        assert respuesta.status_code == 201
        assert respuesta.json()["estadoMeta"] == "PENDING"

        respuesta = await cliente.get("/messaging/plataforma/plantilla-otp")
        assert respuesta.status_code == 200
        assert len(respuesta.json()) == 1
    finally:
        await _limpiar(email)
