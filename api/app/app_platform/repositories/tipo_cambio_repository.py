"""Acceso a datos puro de `tipos_cambio`. `obtener_vigente` es el único
método de lectura de "TRM vigente" en todo el proyecto."""

from datetime import date

from sqlalchemy import or_, select

from app.app_platform.models.tipo_cambio_model import TipoCambio
from app.core.database.repository_base import RepositoryBase


class TipoCambioRepository(RepositoryBase[TipoCambio]):
    model = TipoCambio

    async def obtener_vigente(self, par: str, fecha: date) -> TipoCambio | None:
        resultado = await self.session.execute(
            select(TipoCambio).where(
                TipoCambio.par == par,
                TipoCambio.vigente_desde <= fecha,
                or_(
                    TipoCambio.vigente_hasta.is_(None),
                    TipoCambio.vigente_hasta >= fecha,
                ),
            )
        )
        return resultado.scalars().first()

    async def obtener_historico(self, par: str) -> list[TipoCambio]:
        resultado = await self.session.execute(
            select(TipoCambio)
            .where(TipoCambio.par == par)
            .order_by(TipoCambio.vigente_desde)
        )
        return list(resultado.scalars().all())

    async def obtener_abierto(self, par: str) -> TipoCambio | None:
        resultado = await self.session.execute(
            select(TipoCambio).where(
                TipoCambio.par == par, TipoCambio.vigente_hasta.is_(None)
            )
        )
        return resultado.scalars().first()
