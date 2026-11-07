"""Acceso a datos de `Suscripcion`. Tenant-scoped vía `TenantScopedRepository`,
salvo `obtener_vencidas_global`: el cobro recurrente corre en segundo plano,
sin tenant en contexto, y necesita barrer todos los tenants con un cobro
vencido hoy -- mismo patrón que los demás métodos `_global` del proyecto
(ver `usuario_repository.py`)."""

from datetime import date

from sqlalchemy import select

from app.billing.enums.billing_enums import EstadoSuscripcion
from app.billing.models.suscripcion_model import Suscripcion
from app.core.database.tenant_repository import TenantScopedRepository

_ESTADOS_COBRABLES = (EstadoSuscripcion.activa, EstadoSuscripcion.en_reintento)


class SuscripcionRepository(TenantScopedRepository[Suscripcion]):
    model = Suscripcion

    async def obtener_activa_del_tenant(self) -> Suscripcion | None:
        resultado = await self.session.execute(
            self.scoped()
            .where(Suscripcion.estado.in_(_ESTADOS_COBRABLES))
            .order_by(Suscripcion.id.desc())
        )
        return resultado.scalars().first()

    async def obtener_vencidas_global(self, fecha: date) -> list[Suscripcion]:
        resultado = await self.session.execute(
            select(Suscripcion).where(
                Suscripcion.estado.in_(_ESTADOS_COBRABLES),
                Suscripcion.proxima_fecha_cobro <= fecha,
            )
        )
        return list(resultado.scalars().all())
