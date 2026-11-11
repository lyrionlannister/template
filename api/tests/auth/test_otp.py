"""`OtpService._despachar_whatsapp` con `MetaClient`/plantilla/costo
reemplazados por dobles -- no hay red real ni dependencia de una plantilla
aprobada en Meta."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.app_platform.models.plan_model import Plan
from app.auth.enums.auth_enums import EstadoTenant
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.auth.repositories.codigo_otp_repository import CodigoOtpRepository
from app.auth.services.otp_service import OtpService
from app.core.config.settings import get_settings
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant


class _MetaClientFalso:
    def __init__(self):
        self.enviado: dict | None = None

    async def enviar_plantilla(self, **kwargs) -> None:
        self.enviado = kwargs


class _PlantillaServiceFalso:
    def __init__(self, plantilla=None):
        self._plantilla = plantilla

    async def obtener_aprobada(self):
        return self._plantilla


class _PlantillaFalsa:
    nombre = "pulso_otp"
    idioma = "es"


class _CostoServicioFalso:
    async def costo_vigente(self, *args, **kwargs):
        return None


async def _crear_usuario(telefono: str | None) -> int:
    async with async_session_factory() as session:
        plan = Plan(
            nombre=f"plan-prueba-{uuid.uuid4().hex[:8]}",
            precio_mensual_cop=100_000,
            limite_filas_importacion=1000,
            mensajes_marketing_incluidos=1000,
            precio_marketing_mensaje_cop=90,
            precio_utility_mensaje_cop=15,
            max_usuarios=1,
            max_whatsapp_numeros=1,
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        tenant = Tenant(
            nombre=f"tenant-prueba-{uuid.uuid4().hex[:8]}",
            estado=EstadoTenant.activo,
            trial_fin=datetime.now(UTC) + timedelta(days=14),
            plan_id=plan.id,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        with set_current_tenant(tenant.id):
            usuario = Usuario(
                tenant_id=tenant.id,
                email=f"otp-{uuid.uuid4().hex[:12]}@test.com",
                password_hash="hash",
                telefono=telefono,
            )
            session.add(usuario)
            await session.commit()
            await session.refresh(usuario)
            return usuario.id


def _servicio(session, *, meta_client, plantilla_service) -> OtpService:
    return OtpService(
        CodigoOtpRepository(session),
        meta_client=meta_client,
        plantilla_service=plantilla_service,
        costo_canal_service=_CostoServicioFalso(),
    )


async def test_sin_telefono_lanza_valueerror():
    usuario_id = await _crear_usuario(telefono=None)
    async with async_session_factory() as session:
        servicio = _servicio(
            session,
            meta_client=_MetaClientFalso(),
            plantilla_service=_PlantillaServiceFalso(_PlantillaFalsa()),
        )
        with pytest.raises(ValueError):
            await servicio._despachar_whatsapp(usuario_id, "123456")


async def test_sin_plantilla_aprobada_lanza_valueerror():
    usuario_id = await _crear_usuario(telefono="+573001234567")
    async with async_session_factory() as session:
        servicio = _servicio(
            session,
            meta_client=_MetaClientFalso(),
            plantilla_service=_PlantillaServiceFalso(None),
        )
        with pytest.raises(ValueError):
            await servicio._despachar_whatsapp(usuario_id, "123456")


async def test_envia_la_plantilla_con_el_codigo_como_parametro():
    usuario_id = await _crear_usuario(telefono="+573001234567")
    meta_falso = _MetaClientFalso()
    async with async_session_factory() as session:
        servicio = _servicio(
            session,
            meta_client=meta_falso,
            plantilla_service=_PlantillaServiceFalso(_PlantillaFalsa()),
        )
        await servicio._despachar_whatsapp(usuario_id, "123456")

    s = get_settings().messaging
    assert meta_falso.enviado == {
        "phone_number_id": s.meta_platform_phone_number_id,
        "token_acceso": s.meta_access_token.get_secret_value(),
        "telefono_destino": "+573001234567",
        "nombre_plantilla": "pulso_otp",
        "idioma": "es",
        "parametros_posicionales": ["123456"],
    }
