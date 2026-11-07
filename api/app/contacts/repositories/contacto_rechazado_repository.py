"""Acceso a datos puro de `ContactoRechazado`. Tenant-scoped: toda fila
rechazada pertenece a un tenant y se lee/escribe siempre en su contexto."""

from app.contacts.models.contacto_rechazado_model import ContactoRechazado
from app.core.database.tenant_repository import TenantScopedRepository


class ContactoRechazadoRepository(TenantScopedRepository[ContactoRechazado]):
    model = ContactoRechazado
