"""Acceso a datos puro de `ImportacionContacto`. Tenant-scoped: toda
importación pertenece a un tenant y se lee/escribe siempre en su
contexto."""

from app.contacts.models.importacion_contacto_model import ImportacionContacto
from app.core.database.tenant_repository import TenantScopedRepository


class ImportacionContactoRepository(TenantScopedRepository[ImportacionContacto]):
    model = ImportacionContacto
