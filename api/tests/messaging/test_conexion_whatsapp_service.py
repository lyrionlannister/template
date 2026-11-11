"""Tests contra la base real (mismo patrón que
`tests/templates/test_templates_service.py`): límite de plan, número ya
tomado por otro tenant, cifrado real del token persistido, aislamiento
cross-tenant. El cliente Meta se reemplaza por un doble simple -- no hay
red real en un test de servicio."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.app_platform.exceptions import LimiteDePlanError
from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.auth.dependencies import get_auth_service
from app.auth.enums.auth_enums import EstadoTenant, RolUsuario
from app.auth.models.tenant_model import Tenant
from app.auth.schemas.sesion_schema import SesionUsuario
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant
from app.messaging.exceptions import (
    ConexionWhatsappNoEncontradaError,
    NumeroYaConectadoError,
)
from app.messaging.repositories.conexion_whatsapp_repository import (
    ConexionWhatsappRepository,
)
from app.messaging.services.conexion_whatsapp_service import ConexionWhatsappService


class _MetaClientFalso:
    def __init__(self, access_token="tok-plano-del-tenant", numero="+573001234567"):
        self.access_token = access_token
        self.numero = numero
        self.llamadas_intercambio = 0

    async def intercambiar_code_por_token(self, code: str) -> dict:
        self.llamadas_intercambio += 1
        return {"access_token": self.access_token}

    async def obtener_numero_telefono(
        self, phone_number_id: str, token_acceso: str
    ) -> str:
        return self.numero


async def _crear_tenant(max_whatsapp_numeros: int = 1) -> int:
    async with async_session_factory() as session:
        plan = Plan(
            nombre=f"plan-prueba-{uuid.uuid4().hex[:8]}",
            precio_mensual_cop=100_000,
            limite_filas_importacion=1000,
            mensajes_marketing_incluidos=1000,
            precio_marketing_mensaje_cop=90,
            precio_utility_mensaje_cop=15,
            max_usuarios=1,
            max_whatsapp_numeros=max_whatsapp_numeros,
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
        return tenant.id


def _sesion_de(tenant_id: int) -> SesionUsuario:
    return SesionUsuario(
        usuario_id=1,
        tenant_id=tenant_id,
        email="prueba@test.com",
        rol=RolUsuario.administrador,
        mfa_habilitado=False,
    )


def _crear_service(session, meta_client=None) -> ConexionWhatsappService:
    parametro_comercial_service = ParametroComercialService(session)
    plan_service = PlanService(
        session,
        CostoCanalService(session),
        TipoCambioService(session),
        parametro_comercial_service,
    )
    auth_service = get_auth_service(session, plan_service, parametro_comercial_service)
    return ConexionWhatsappService(
        session,
        ConexionWhatsappRepository(session),
        meta_client or _MetaClientFalso(),
        auth_service,
        plan_service,
    )


async def test_conectar_cifra_el_token_antes_de_persistirlo():
    tenant_id = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_service(session)
            conexion = await servicio.conectar(
                _sesion_de(tenant_id),
                "code-abc",
                "waba-1",
                f"phone-{uuid.uuid4().hex[:8]}",
            )

    assert conexion.token_acceso_cifrado != "tok-plano-del-tenant"
    assert conexion.numero_telefono == "+573001234567"


async def test_limite_de_plan_bloquea_antes_de_llamar_a_meta():
    tenant_id = await _crear_tenant(max_whatsapp_numeros=1)
    meta_falso = _MetaClientFalso()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_service(session, meta_falso)
            await servicio.conectar(
                _sesion_de(tenant_id),
                "code-1",
                "waba-1",
                f"phone-{uuid.uuid4().hex[:8]}",
            )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_service(session, meta_falso)
            with pytest.raises(LimiteDePlanError):
                await servicio.conectar(
                    _sesion_de(tenant_id),
                    "code-2",
                    "waba-1",
                    f"phone-{uuid.uuid4().hex[:8]}",
                )
    assert meta_falso.llamadas_intercambio == 1


async def test_numero_ya_conectado_por_otro_tenant_se_rechaza():
    tenant_a = await _crear_tenant()
    tenant_b = await _crear_tenant()
    phone_number_id = f"phone-{uuid.uuid4().hex[:8]}"

    async with async_session_factory() as session:
        with set_current_tenant(tenant_a):
            servicio = _crear_service(session)
            await servicio.conectar(
                _sesion_de(tenant_a), "code-a", "waba-a", phone_number_id
            )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_b):
            servicio = _crear_service(session)
            with pytest.raises(NumeroYaConectadoError):
                await servicio.conectar(
                    _sesion_de(tenant_b), "code-b", "waba-b", phone_number_id
                )


async def test_tenant_sin_conexion_lanza_error_al_pedir_la_de_envio():
    tenant_id = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            servicio = _crear_service(session)
            with pytest.raises(ConexionWhatsappNoEncontradaError):
                await servicio.obtener_para_envio()


async def test_tenant_no_ve_la_conexion_de_otro_tenant():
    tenant_a = await _crear_tenant()
    tenant_b = await _crear_tenant()

    async with async_session_factory() as session:
        with set_current_tenant(tenant_a):
            servicio = _crear_service(session)
            await servicio.conectar(
                _sesion_de(tenant_a),
                "code-a",
                "waba-a",
                f"phone-{uuid.uuid4().hex[:8]}",
            )

    async with async_session_factory() as session:
        with set_current_tenant(tenant_b):
            servicio = _crear_service(session)
            with pytest.raises(ConexionWhatsappNoEncontradaError):
                await servicio.obtener_para_envio()
