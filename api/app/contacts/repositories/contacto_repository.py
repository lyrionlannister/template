"""Acceso a datos puro de `Contacto`. Tenant-scoped: todo contacto
pertenece a un tenant y se lee/escribe siempre en su contexto."""

from app.contacts.models.contacto_model import Contacto
from app.core.database.tenant_repository import TenantScopedRepository


class ContactoRepository(TenantScopedRepository[Contacto]):
    model = Contacto
