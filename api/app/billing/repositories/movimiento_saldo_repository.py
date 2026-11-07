"""Acceso a datos de `MovimientoSaldo`. Tenant-scoped vía
`TenantScopedRepository`, salvo `obtener_por_referencia_global`: el webhook
llega sin tenant en contexto, igual que `CobroRepository` (ver su docstring)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.billing.enums.billing_enums import (
    ConceptoMovimientoSaldo,
    EstadoTransaccionPago,
)
from app.billing.models.movimiento_saldo_model import MovimientoSaldo
from app.core.database.tenant_repository import TenantScopedRepository


class MovimientoSaldoRepository(TenantScopedRepository[MovimientoSaldo]):
    model = MovimientoSaldo

    async def obtener_por_referencia_global(
        self, referencia: str
    ) -> MovimientoSaldo | None:
        resultado = await self.session.execute(
            select(MovimientoSaldo).where(MovimientoSaldo.referencia == referencia)
        )
        return resultado.scalars().first()

    async def obtener_por_public_id(self, public_id: UUID) -> MovimientoSaldo | None:
        resultado = await self.session.execute(
            self.scoped().where(MovimientoSaldo.public_id == public_id)
        )
        return resultado.scalars().first()

    async def listar_recientes(self, limite: int = 20) -> list[MovimientoSaldo]:
        resultado = await self.session.execute(
            self.scoped().order_by(MovimientoSaldo.creado_en.desc()).limit(limite)
        )
        return list(resultado.scalars().all())

    async def calcular_saldo_disponible(self) -> Decimal:
        """Suma de recargas aprobadas. Sin `consumo` todavía (llega en la
        fase de mensajería), así que por ahora el saldo es exactamente eso:
        lo recargado y confirmado."""

        query = (
            self.scoped()
            .with_only_columns(func.coalesce(func.sum(MovimientoSaldo.monto_cop), 0))
            .where(
                MovimientoSaldo.concepto == ConceptoMovimientoSaldo.recarga,
                MovimientoSaldo.estado == EstadoTransaccionPago.aprobada,
            )
        )
        resultado = await self.session.execute(query)
        return Decimal(resultado.scalar_one())
