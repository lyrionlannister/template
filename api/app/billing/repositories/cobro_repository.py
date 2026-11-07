"""Acceso a datos de `Cobro`. Tenant-scoped vía `TenantScopedRepository`,
salvo `obtener_por_referencia_global`: el webhook de la pasarela llega sin
tenant en contexto (identifica el cobro por `referencia`, que es como
`Usuario.obtener_por_email_global` identifica un usuario por correo antes de
saber a qué tenant pertenece -- mismo patrón, ver `usuario_repository.py`).
Ningún otro método de este repository se salta `scoped()`."""

from sqlalchemy import select

from app.billing.models.cobro_model import Cobro
from app.core.database.tenant_repository import TenantScopedRepository


class CobroRepository(TenantScopedRepository[Cobro]):
    model = Cobro

    async def obtener_por_referencia_global(self, referencia: str) -> Cobro | None:
        resultado = await self.session.execute(
            select(Cobro).where(Cobro.referencia == referencia)
        )
        return resultado.scalars().first()
