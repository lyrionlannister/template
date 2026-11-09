"""`ContactoRepository` ejecutando `FiltroAudiencia` contra Postgres real:
cada operador, el cast seguro de `gt`/`lt` sobre variables (texto en BD),
`exists`/`not_exists`, y que `listar_claves_variables` es tenant-scoped."""

import uuid
from datetime import UTC, datetime, timedelta

from app.app_platform.models.plan_model import Plan
from app.auth.enums.auth_enums import EstadoTenant
from app.auth.models.tenant_model import Tenant
from app.contacts.models.contacto_model import Contacto
from app.contacts.repositories.contacto_repository import ContactoRepository
from app.contacts.schemas.filtro_schema import Condicion, FiltroAudiencia
from app.core.database.session import async_session_factory
from app.core.database.tenant_context import set_current_tenant


async def _crear_tenant() -> int:
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
        return tenant.id


async def _crear_contacto(tenant_id: int, telefono: str, variables: dict) -> int:
    async with async_session_factory() as session:
        contacto = Contacto(tenant_id=tenant_id, telefono=telefono, variables=variables)
        session.add(contacto)
        await session.commit()
        await session.refresh(contacto)
        return contacto.id


def _filtro(field: str, op: str, value=None) -> FiltroAudiencia:
    kwargs = {"field": field, "op": op}
    if value is not None:
        kwargs["value"] = value
    return FiltroAudiencia(and_=[Condicion(**kwargs)])


async def test_eq_sobre_variable_filtra_por_valor_exacto() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000001", {"ciudad": "CDMX"})
    await _crear_contacto(tenant_id, "+573000000002", {"ciudad": "Bogota"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            repo = ContactoRepository(session)
            conteo = await repo.contar_por_filtro(
                _filtro("variables.ciudad", "eq", "CDMX")
            )
    assert conteo == 1


async def test_contains_sobre_variable_es_case_insensitive() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000003", {"ciudad": "Ciudad de Mexico"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            repo = ContactoRepository(session)
            conteo = await repo.contar_por_filtro(
                _filtro("variables.ciudad", "contains", "mexico")
            )
    assert conteo == 1


async def test_gt_numerico_sobre_variable_compara_como_numero_no_texto() -> None:
    tenant_id = await _crear_tenant()
    # Comparación lexicográfica (texto) pondría "9" > "80"; numérica no.
    await _crear_contacto(tenant_id, "+573000000004", {"saldo": "9"})
    await _crear_contacto(tenant_id, "+573000000005", {"saldo": "80"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            repo = ContactoRepository(session)
            conteo = await repo.contar_por_filtro(_filtro("variables.saldo", "gt", 50))
    assert conteo == 1


async def test_gt_con_valor_no_numerico_en_bd_no_truena_y_excluye_la_fila() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000006", {"saldo": "no-es-un-numero"})
    await _crear_contacto(tenant_id, "+573000000007", {"saldo": "100"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            repo = ContactoRepository(session)
            conteo = await repo.contar_por_filtro(_filtro("variables.saldo", "gt", 10))
    assert conteo == 1


async def test_exists_y_not_exists_sobre_variable() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573000000008", {"ciudad": "CDMX"})
    await _crear_contacto(tenant_id, "+573000000009", {"plan": "Basico"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            repo = ContactoRepository(session)
            con_ciudad = await repo.contar_por_filtro(
                _filtro("variables.ciudad", "exists")
            )
            sin_ciudad = await repo.contar_por_filtro(
                _filtro("variables.ciudad", "not_exists")
            )
    assert con_ciudad == 1
    assert sin_ciudad == 1


async def test_filtro_sobre_telefono_y_creado_en() -> None:
    tenant_id = await _crear_tenant()
    await _crear_contacto(tenant_id, "+573001112233", {})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_id):
            repo = ContactoRepository(session)
            por_telefono = await repo.contar_por_filtro(
                _filtro("telefono", "contains", "1112233")
            )
            por_fecha = await repo.contar_por_filtro(
                _filtro("creado_en", "lte", datetime.now(UTC).date().isoformat())
            )
    assert por_telefono == 1
    assert por_fecha == 1


async def test_filtro_nunca_trae_contactos_de_otro_tenant() -> None:
    tenant_a = await _crear_tenant()
    tenant_b = await _crear_tenant()
    await _crear_contacto(tenant_a, "+573000000010", {"ciudad": "CDMX"})
    await _crear_contacto(tenant_b, "+573000000011", {"ciudad": "CDMX"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_a):
            repo = ContactoRepository(session)
            ids = await repo.listar_ids_por_filtro(
                _filtro("variables.ciudad", "eq", "CDMX")
            )
    assert len(ids) == 1


async def test_listar_claves_variables_es_tenant_scoped() -> None:
    tenant_a = await _crear_tenant()
    tenant_b = await _crear_tenant()
    await _crear_contacto(tenant_a, "+573000000012", {"ciudad": "CDMX", "saldo": "1"})
    await _crear_contacto(tenant_b, "+573000000013", {"producto": "X"})

    async with async_session_factory() as session:
        with set_current_tenant(tenant_a):
            repo = ContactoRepository(session)
            claves = await repo.listar_claves_variables()
    assert set(claves) == {"ciudad", "saldo"}
