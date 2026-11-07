"""Acceso a datos puro de `parametros_comerciales`. `obtener_vigente` es el
único método de lectura de "valor vigente de un parámetro" del proyecto."""

from datetime import date

from sqlalchemy import or_, select

from app.app_platform.models.parametro_comercial_model import ParametroComercial
from app.core.database.repository_base import RepositoryBase


class ParametroComercialRepository(RepositoryBase[ParametroComercial]):
    model = ParametroComercial

    async def obtener_vigente(
        self, clave: str, fecha: date
    ) -> ParametroComercial | None:
        resultado = await self.session.execute(
            select(ParametroComercial).where(
                ParametroComercial.clave == clave,
                ParametroComercial.vigente_desde <= fecha,
                or_(
                    ParametroComercial.vigente_hasta.is_(None),
                    ParametroComercial.vigente_hasta >= fecha,
                ),
            )
        )
        return resultado.scalars().first()

    async def obtener_historico(self, clave: str) -> list[ParametroComercial]:
        resultado = await self.session.execute(
            select(ParametroComercial)
            .where(ParametroComercial.clave == clave)
            .order_by(ParametroComercial.vigente_desde)
        )
        return list(resultado.scalars().all())

    async def obtener_abierto(self, clave: str) -> ParametroComercial | None:
        resultado = await self.session.execute(
            select(ParametroComercial).where(
                ParametroComercial.clave == clave,
                ParametroComercial.vigente_hasta.is_(None),
            )
        )
        return resultado.scalars().first()
