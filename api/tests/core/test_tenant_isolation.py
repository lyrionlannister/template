"""Prueba central del núcleo: una consulta de un tenant no debe poder ver
datos de otro, y sin un tenant fijado en contexto la consulta falla en vez
de devolver todo (fail-closed, ver tenant_context.py).

El modelo `Nota` es solo de prueba, con su propia `DeclarativeBase` —no la
`Base` real de la app— para no ensuciar el metadata que usa Alembic.
"""

import pytest
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.database.base import IdMixin, TenantScopedMixin
from app.core.database.session import async_session_factory, engine
from app.core.database.tenant_context import (
    TenantContextError,
    allow_system_scope,
    set_current_tenant,
)
from app.core.database.tenant_repository import TenantScopedRepository
from app.core.valkey.client import valkey_client


class _NotaBase(DeclarativeBase):
    pass


class Nota(_NotaBase, TenantScopedMixin, IdMixin):
    __tablename__ = "notas_de_prueba_aislamiento"

    texto: Mapped[str] = mapped_column("texto")


class NotaRepository(TenantScopedRepository[Nota]):
    model = Nota


@pytest.fixture(autouse=True)
async def _tabla_de_prueba():
    async with engine.begin() as conn:
        await conn.run_sync(_NotaBase.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(_NotaBase.metadata.drop_all)
    async for clave in valkey_client.scan_iter(match="notas_de_prueba_aislamiento:*"):
        await valkey_client.delete(clave)


async def test_consulta_de_un_tenant_no_devuelve_datos_de_otro():
    async with async_session_factory() as session:
        session.add_all(
            [
                Nota(tenant_id=1, texto="de tenant 1"),
                Nota(tenant_id=2, texto="de tenant 2"),
            ]
        )
        await session.commit()

    async with async_session_factory() as session:
        repo = NotaRepository(session)
        with set_current_tenant(1):
            filas = (await session.execute(repo.scoped())).scalars().all()

    assert [fila.texto for fila in filas] == ["de tenant 1"]


async def test_sin_tenant_en_contexto_falla_en_vez_de_devolver_todo():
    async with async_session_factory() as session:
        repo = NotaRepository(session)
        with pytest.raises(TenantContextError):
            repo.scoped()


async def test_bypass_de_administrador_del_sistema_tambien_exige_tenant_explicito():
    async with async_session_factory() as session:
        repo = NotaRepository(session)
        with allow_system_scope(), pytest.raises(TenantContextError):
            repo.scoped()


async def test_get_by_id_cachea_y_el_segundo_llamado_no_toca_postgres():
    async with async_session_factory() as session:
        with set_current_tenant(1):
            repo = NotaRepository(session)
            nota = await repo.add(Nota(tenant_id=1, texto="original"))
            await session.commit()

            primera = await repo.get_by_id(nota.id)
            assert primera.texto == "original"

            # Cambio directo en Postgres, sin pasar por el repository: si
            # get_by_id vuelve a leer de ahí en vez del cache, lo vería.
            await session.execute(
                Nota.__table__.update()
                .where(Nota.id == nota.id)
                .values(texto="cambiado por fuera")
            )
            await session.commit()

            segunda = await repo.get_by_id(nota.id)
            assert segunda.texto == "original"


async def test_update_invalida_el_cache():
    async with async_session_factory() as session:
        with set_current_tenant(1):
            repo = NotaRepository(session)
            nota = await repo.add(Nota(tenant_id=1, texto="v1"))
            await session.commit()

            await repo.get_by_id(nota.id)  # cachea v1

            nota.texto = "v2"
            await repo.update(nota)
            await session.commit()

            releida = await repo.get_by_id(nota.id)
            assert releida.texto == "v2"


async def test_get_by_id_no_filtra_fila_de_otro_tenant():
    async with async_session_factory() as session:
        with set_current_tenant(1):
            repo = NotaRepository(session)
            nota_tenant_1 = await repo.add(Nota(tenant_id=1, texto="tenant 1"))
            await session.commit()

        with set_current_tenant(2):
            repo = NotaRepository(session)
            assert await repo.get_by_id(nota_tenant_1.id) is None
