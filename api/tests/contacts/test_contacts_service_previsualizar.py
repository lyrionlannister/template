"""Tests de `ContactsService.previsualizar`: valida tipo real, resuelve el
límite de filas del plan vigente del tenant, cachea en Valkey solo si
pasa, y rechaza completo -- sin cachear nada -- si excede el límite o si
el contenido real no coincide con la extensión declarada."""

import io
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.models.plan_model import Plan
from app.app_platform.services.costo_canal_service import CostoCanalService
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.app_platform.services.tipo_cambio_service import TipoCambioService
from app.auth.dependencies import get_auth_service
from app.auth.enums.auth_enums import EstadoTenant
from app.auth.models.tenant_model import Tenant
from app.contacts.exceptions import (
    LimiteDeFilasExcedidoError,
    TipoDeArchivoNoCoincideError,
)
from app.contacts.repositories.configuracion_contactos_repository import (
    ConfiguracionContactosRepository,
)
from app.contacts.repositories.conflicto_variable_repository import (
    ConflictoVariableRepository,
)
from app.contacts.repositories.contacto_repository import ContactoRepository
from app.contacts.repositories.importacion_contacto_repository import (
    ImportacionContactoRepository,
)
from app.contacts.services.contacts_service import ContactsService
from app.core.database.session import async_session_factory
from app.core.valkey.client import valkey_client


class _ArchivoSubido:
    """Stub mínimo de `UploadFile`: solo `.filename` y `.read(n)` async,
    lo único que `ContactsService` usa."""

    def __init__(self, filename: str, contenido: bytes) -> None:
        self.filename = filename
        self._buffer = io.BytesIO(contenido)

    async def read(self, size: int) -> bytes:
        return self._buffer.read(size)


async def _crear_plan(limite_filas: int) -> int:
    async with async_session_factory() as session:
        plan = Plan(
            nombre=f"plan-prueba-{uuid.uuid4().hex[:8]}",
            precio_mensual_cop=100_000,
            limite_filas_importacion=limite_filas,
            mensajes_marketing_incluidos=1000,
            precio_marketing_mensaje_cop=90,
            precio_utility_mensaje_cop=15,
            max_usuarios=1,
            max_whatsapp_numeros=1,
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        return plan.id


async def _crear_tenant(plan_id: int) -> int:
    async with async_session_factory() as session:
        tenant = Tenant(
            nombre=f"tenant-prueba-{uuid.uuid4().hex[:8]}",
            estado=EstadoTenant.activo,
            trial_fin=datetime.now(UTC) + timedelta(days=14),
            plan_id=plan_id,
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        return tenant.id


def _crear_service(session: AsyncSession) -> ContactsService:
    parametro_comercial_service = ParametroComercialService(session)
    plan_service = PlanService(
        session,
        CostoCanalService(session),
        TipoCambioService(session),
        parametro_comercial_service,
    )
    auth_service = get_auth_service(session, plan_service, parametro_comercial_service)
    return ContactsService(
        session,
        auth_service,
        plan_service,
        parametro_comercial_service,
        ContactoRepository(session),
        ImportacionContactoRepository(session),
        ConfiguracionContactosRepository(session),
        ConflictoVariableRepository(session),
    )


async def test_previsualizar_csv_en_el_limite_exacto_cachea_en_valkey() -> None:
    plan_id = await _crear_plan(limite_filas=1)
    tenant_id = await _crear_tenant(plan_id)
    archivo = _ArchivoSubido("contactos.csv", b"telefono,nombre\n+573001112233,Ana\n")

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        resultado = await servicio.previsualizar(tenant_id, archivo)

    assert resultado.total_filas == 1
    assert resultado.columnas == ["telefono", "nombre"]
    assert resultado.muestra == [{"telefono": "+573001112233", "nombre": "Ana"}]

    clave = f"importacion:preview:{tenant_id}:{resultado.preview_id}"
    crudo = await valkey_client.get(clave)
    assert crudo is not None
    assert json.loads(crudo)["formato"] == "csv"
    await valkey_client.delete(clave)


async def test_previsualizar_rechaza_archivo_que_excede_limite_sin_cachear() -> None:
    plan_id = await _crear_plan(limite_filas=2)
    tenant_id = await _crear_tenant(plan_id)
    contenido = "telefono\n" + "\n".join(f"+57300000{i:04d}" for i in range(3))
    archivo = _ArchivoSubido("contactos.csv", contenido.encode("utf-8"))
    patron = f"importacion:preview:{tenant_id}:*"

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with pytest.raises(LimiteDeFilasExcedidoError):
            await servicio.previsualizar(tenant_id, archivo)

    claves = [clave async for clave in valkey_client.scan_iter(match=patron)]
    assert claves == []


async def test_previsualizar_rechaza_tipo_real_que_no_coincide_con_extension() -> None:
    plan_id = await _crear_plan(limite_filas=10)
    tenant_id = await _crear_tenant(plan_id)
    # Firma real de ZIP/XLSX con extensión .csv mentirosa.
    archivo = _ArchivoSubido("contactos.csv", b"PK\x03\x04" + b"\x00" * 20)
    patron = f"importacion:preview:{tenant_id}:*"

    async with async_session_factory() as session:
        servicio = _crear_service(session)
        with pytest.raises(TipoDeArchivoNoCoincideError):
            await servicio.previsualizar(tenant_id, archivo)

    claves = [clave async for clave in valkey_client.scan_iter(match=patron)]
    assert claves == []
