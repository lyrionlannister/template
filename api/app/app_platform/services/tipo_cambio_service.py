"""Reglas de negocio de la TRM. `valor_vigente` NO exige alcance de sistema:
lo usa internamente cualquier cálculo de margen o de precio corriendo en
contexto de un tenant normal (igual que `CostoCanalService.costo_vigente`).
`historico`/`registrar` sí, son del panel de administrador."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.models.tipo_cambio_model import TipoCambio
from app.app_platform.repositories.tipo_cambio_repository import TipoCambioRepository
from app.core.database.tenant_context import is_system_scope


class AccesoDeAdministradorRequeridoError(PermissionError):
    pass


def _exigir_alcance_de_sistema() -> None:
    if not is_system_scope():
        raise AccesoDeAdministradorRequeridoError(
            "Esta operación requiere alcance de administrador del sistema."
        )


class TipoCambioService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TipoCambioRepository(session)

    async def valor_vigente(self, par: str, fecha: date) -> TipoCambio | None:
        return await self.repository.obtener_vigente(par, fecha)

    async def historico(self, par: str) -> list[TipoCambio]:
        _exigir_alcance_de_sistema()
        return await self.repository.obtener_historico(par)

    async def registrar(
        self, par: str, valor: Decimal, fuente: str, vigente_desde: date
    ) -> TipoCambio:
        _exigir_alcance_de_sistema()
        abierto = await self.repository.obtener_abierto(par)
        if abierto is not None:
            abierto.vigente_hasta = vigente_desde

        nuevo = TipoCambio(
            par=par,
            valor=valor,
            fuente=fuente,
            vigente_desde=vigente_desde,
            vigente_hasta=None,
        )
        creado = await self.repository.add(nuevo)
        await self.session.commit()
        return creado
