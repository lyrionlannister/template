"""Criterio de aceptación del Prompt 03 sobre el límite de usuarios: con
Esencial no se puede crear un segundo usuario, y subir `max_usuarios` desde
el panel lo permite sin tocar código."""

import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.auth.models.codigo_otp_model import CodigoOtp
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import allow_system_scope
from app.core.security.token_service import TokenService
from app.core.valkey.client import valkey_client
from main import app

_PASSWORD = "Clave-Segura123"


def _email_de_prueba() -> str:
    return f"test-invitar-{uuid.uuid4().hex[:12]}@acme.com"


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
    token = cliente.cookies.get("access_token")
    payload = TokenService().verificar_access_token(token)
    return int(payload["sub"])


async def _usuario_id_por_email(email: str) -> int:
    async with async_session_factory() as session:
        resultado = await session.execute(
            select(Usuario.id).where(Usuario.email == email.lower())
        )
        return resultado.scalar_one()


async def _registrar_y_verificar_mfa(cliente: AsyncClient, email: str, capsys) -> int:
    respuesta = await cliente.post(
        "/auth/registro",
        json={
            "nombreOrganizacion": "Empresa de prueba",
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


async def _limpiar(
    email_admin: str, email_invitado: str, usuario_ids: list[int]
) -> None:
    async with async_session_factory() as session:
        for usuario_id in usuario_ids:
            await session.execute(
                delete(CodigoOtp).where(CodigoOtp.usuario_id == usuario_id)
            )
        resultado = await session.execute(
            delete(Usuario)
            .where(Usuario.id.in_(usuario_ids))
            .returning(Usuario.tenant_id)
        )
        tenants_id = {fila for fila in resultado.scalars().all()}
        for tenant_id in tenants_id:
            await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
    for usuario_id in usuario_ids:
        for clave in (
            f"refresh:{usuario_id}",
            f"session:{usuario_id}",
            f"mfa_verified:{usuario_id}",
            f"otp-intentos:whatsapp:{usuario_id}",
        ):
            await valkey_client.delete(clave)
    for email in (email_admin, email_invitado):
        await valkey_client.delete(f"login-fail:{email}")


async def test_esencial_bloquea_segundo_usuario_y_subir_limite_lo_permite(
    cliente, capsys
):
    email_admin = _email_de_prueba()
    email_invitado = _email_de_prueba()
    usuario_ids: list[int] = []
    max_usuarios_original = None

    def _servicio(session) -> PlanService:
        return PlanService(
            session,
            CostoCanalService(session),
            TipoCambioService(session),
            ParametroComercialService(session),
        )

    async with async_session_factory() as session:
        with allow_system_scope():
            plan = await _servicio(session).obtener_por_nombre("Esencial")
            assert plan is not None
            max_usuarios_original = plan.max_usuarios
            public_id_plan = plan.public_id

    try:
        usuario_id_admin = await _registrar_y_verificar_mfa(
            cliente, email_admin, capsys
        )
        usuario_ids.append(usuario_id_admin)

        rechazo = await cliente.post(
            "/auth/usuarios",
            json={"email": email_invitado, "password": _PASSWORD},
        )
        assert rechazo.status_code == 409

        async with async_session_factory() as session:
            with allow_system_scope():
                await _servicio(session).actualizar(public_id_plan, {"max_usuarios": 2})

        permitido = await cliente.post(
            "/auth/usuarios",
            json={"email": email_invitado, "password": _PASSWORD},
        )
        assert permitido.status_code == 201
        usuario_ids.append(await _usuario_id_por_email(email_invitado))
    finally:
        async with async_session_factory() as session:
            with allow_system_scope():
                await _servicio(session).actualizar(
                    public_id_plan, {"max_usuarios": max_usuarios_original}
                )
        await _limpiar(email_admin, email_invitado, usuario_ids)
