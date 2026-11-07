"""Acceso a datos puro de `costos_canal`.

`obtener_vigente` es el único método de lectura de "costo vigente" en todo
el proyecto: ningún otro código arma su propia query sobre esta tabla para
esa pregunta — así hay una sola definición de "vigente".
"""

from datetime import date

from sqlalchemy import or_, select

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.app_platform.models.costo_canal_model import CostoCanal
from app.core.database.repository_base import RepositoryBase


class CostoCanalRepository(RepositoryBase[CostoCanal]):
    model = CostoCanal

    async def obtener_vigente(
        self,
        canal: CanalMensajeria,
        categoria: CategoriaMensaje | None,
        fecha: date,
    ) -> CostoCanal | None:
        resultado = await self.session.execute(
            select(CostoCanal).where(
                CostoCanal.canal == canal,
                CostoCanal.categoria == categoria,
                CostoCanal.vigente_desde <= fecha,
                or_(
                    CostoCanal.vigente_hasta.is_(None),
                    CostoCanal.vigente_hasta >= fecha,
                ),
            )
        )
        return resultado.scalars().first()

    async def obtener_historico(
        self, canal: CanalMensajeria, categoria: CategoriaMensaje | None
    ) -> list[CostoCanal]:
        resultado = await self.session.execute(
            select(CostoCanal)
            .where(CostoCanal.canal == canal, CostoCanal.categoria == categoria)
            .order_by(CostoCanal.vigente_desde)
        )
        return list(resultado.scalars().all())

    async def obtener_abierto(
        self, canal: CanalMensajeria, categoria: CategoriaMensaje | None
    ) -> CostoCanal | None:
        resultado = await self.session.execute(
            select(CostoCanal).where(
                CostoCanal.canal == canal,
                CostoCanal.categoria == categoria,
                CostoCanal.vigente_hasta.is_(None),
            )
        )
        return resultado.scalars().first()
