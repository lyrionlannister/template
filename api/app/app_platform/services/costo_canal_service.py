"""Reglas de negocio del histórico de costos por canal.

`registrar_costo` y `historico` son operaciones del panel de administrador
del sistema: exigen `is_system_scope()` (ver `tenant_context.py` del
núcleo). `costo_vigente` NO lo exige — lo usa internamente cualquier
cálculo de margen o de precio (billing, messaging) corriendo en contexto de
un tenant normal; restringirlo a alcance de sistema rompería ese uso.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.models.costo_canal_model import CostoCanal
from app.app_platform.repositories.costo_canal_repository import (
    CostoCanalRepository,
)
from app.core.database.tenant_context import is_system_scope


class AccesoDeAdministradorRequeridoError(PermissionError):
    pass


def _exigir_alcance_de_sistema() -> None:
    if not is_system_scope():
        raise AccesoDeAdministradorRequeridoError(
            "Esta operación requiere alcance de administrador del sistema."
        )


class CostoCanalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CostoCanalRepository(session)

    async def costo_vigente(
        self,
        canal: CanalMensajeria,
        categoria: CategoriaMensaje | None,
        fecha: date,
    ) -> CostoCanal | None:
        return await self.repository.obtener_vigente(canal, categoria, fecha)

    async def historico(
        self, canal: CanalMensajeria, categoria: CategoriaMensaje | None
    ) -> list[CostoCanal]:
        _exigir_alcance_de_sistema()
        return await self.repository.obtener_historico(canal, categoria)

    async def registrar_costo(
        self,
        canal: CanalMensajeria,
        categoria: CategoriaMensaje | None,
        proveedor: str,
        costo_unitario: Decimal,
        moneda: str,
        vigente_desde: date,
        fuente: str,
    ) -> CostoCanal:
        _exigir_alcance_de_sistema()

        abierto = await self.repository.obtener_abierto(canal, categoria)
        if abierto is not None:
            abierto.vigente_hasta = vigente_desde

        nuevo = CostoCanal(
            canal=canal,
            categoria=categoria,
            proveedor=proveedor,
            costo_unitario=costo_unitario,
            moneda=moneda,
            vigente_desde=vigente_desde,
            vigente_hasta=None,
            fuente=fuente,
        )
        creado = await self.repository.add(nuevo)
        await self.session.commit()
        return creado
