"""Acceso a datos puro de `FuenteDePago`. Tenant-scoped: toda fuente de pago
pertenece a un tenant y se lee/escribe siempre en su contexto."""

from app.billing.models.fuente_de_pago_model import FuenteDePago
from app.core.database.tenant_repository import TenantScopedRepository


class FuenteDePagoRepository(TenantScopedRepository[FuenteDePago]):
    model = FuenteDePago
