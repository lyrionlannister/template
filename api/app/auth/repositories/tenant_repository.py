"""Acceso a datos puro de `Tenant`. No es tenant-scoped: es la raíz."""

from app.auth.models.tenant_model import Tenant
from app.core.database.repository_base import RepositoryBase


class TenantRepository(RepositoryBase[Tenant]):
    model = Tenant
