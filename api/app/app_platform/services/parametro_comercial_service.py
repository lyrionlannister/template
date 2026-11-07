"""Reglas de negocio de los parámetros comerciales de valor único.
`valor_vigente` NO exige alcance de sistema: lo usa internamente cualquier
service que necesite trial/onboarding/comisión de Wompi. `historico`/
`registrar` sí, son del panel de administrador."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.models.parametro_comercial_model import ParametroComercial
from app.app_platform.repositories.parametro_comercial_repository import (
    ParametroComercialRepository,
)
from app.core.database.tenant_context import is_system_scope


class AccesoDeAdministradorRequeridoError(PermissionError):
    pass


def _exigir_alcance_de_sistema() -> None:
    if not is_system_scope():
        raise AccesoDeAdministradorRequeridoError(
            "Esta operación requiere alcance de administrador del sistema."
        )


class ParametroComercialService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ParametroComercialRepository(session)

    async def valor_vigente(self, clave: str, fecha: date) -> Decimal | None:
        registro = await self.repository.obtener_vigente(clave, fecha)
        return registro.valor if registro else None

    async def registro_vigente(
        self, clave: str, fecha: date
    ) -> ParametroComercial | None:
        return await self.repository.obtener_vigente(clave, fecha)

    async def historico(self, clave: str) -> list[ParametroComercial]:
        _exigir_alcance_de_sistema()
        return await self.repository.obtener_historico(clave)

    async def registrar(
        self, clave: str, valor: Decimal, fuente: str, vigente_desde: date
    ) -> ParametroComercial:
        _exigir_alcance_de_sistema()
        abierto = await self.repository.obtener_abierto(clave)
        if abierto is not None:
            abierto.vigente_hasta = vigente_desde

        nuevo = ParametroComercial(
            clave=clave,
            valor=valor,
            fuente=fuente,
            vigente_desde=vigente_desde,
            vigente_hasta=None,
        )
        creado = await self.repository.add(nuevo)
        await self.session.commit()
        return creado
