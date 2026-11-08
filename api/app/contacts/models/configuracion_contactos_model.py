"""Configuración de contactos del tenant: una fila por tenant, hoy solo
guarda la política de conflicto de variables al reimportar. Se crea bajo
demanda (lazy) -- un tenant sin fila todavía usa el default `ultimo_gana`,
ver `ContactsService.obtener_politica_conflicto`."""

from sqlalchemy import Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.contacts.enums.contacts_enums import PoliticaConflictoVariables
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class ConfiguracionContactos(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "configuraciones_contactos"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_configuraciones_contactos_tenant"),
    )

    politica_conflicto_variables: Mapped[PoliticaConflictoVariables] = mapped_column(
        "politica_conflicto_variables",
        Enum(PoliticaConflictoVariables, name="politica_conflicto_variables"),
        nullable=False,
        default=PoliticaConflictoVariables.ultimo_gana,
    )
