"""Tenant: organización cliente de Pulso, raíz de aislamiento (`/CLAUDE.md`,
«Multi-tenant siempre»). No hereda `TenantScopedMixin`: es él mismo la raíz,
no un dato que pertenezca a un tenant.

`plan_id` no existe todavía: se agrega como columna + migración cuando el
dominio de planes exista (Prompt 03), no antes.
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.enums.auth_enums import EstadoTenant
from app.core.database.base import Base, IdMixin, TimestampMixin


class Tenant(Base, IdMixin, TimestampMixin):
    __tablename__ = "tenants"

    nombre: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    estado: Mapped[EstadoTenant] = mapped_column(
        "estado", Enum(EstadoTenant, name="estado_tenant"), nullable=False
    )
    trial_fin: Mapped[datetime] = mapped_column(
        "trial_fin", DateTime(timezone=True), nullable=False
    )
