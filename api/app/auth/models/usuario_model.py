"""Usuario de un tenant. El primer usuario de un tenant nuevo (registro) es
siempre `administrador`; invitar usuarios adicionales llega con el límite
de plan (Prompt 03) — no antes, para no exponer un alta sin su límite.
"""

from sqlalchemy import Boolean, Enum, ForeignKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.enums.auth_enums import RolUsuario
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class Usuario(Base, TenantScopedMixin, IdMixin, TimestampMixin):
    __tablename__ = "usuarios"
    __table_args__ = (ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),)

    # Único a nivel global (no por tenant): el login resuelve el tenant a
    # partir del correo, antes de que haya contexto de tenant que filtrar.
    email: Mapped[str] = mapped_column(
        "email", String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(
        "password_hash", String(255), nullable=False
    )
    rol: Mapped[RolUsuario] = mapped_column(
        "rol",
        Enum(RolUsuario, name="rol_usuario"),
        nullable=False,
        default=RolUsuario.administrador,
    )
    mfa_habilitado: Mapped[bool] = mapped_column(
        "mfa_habilitado", Boolean, nullable=False, default=True
    )
    activo: Mapped[bool] = mapped_column(
        "activo", Boolean, nullable=False, default=True
    )
    es_superadmin: Mapped[bool] = mapped_column(
        "es_superadmin", Boolean, nullable=False, default=False
    )
    telefono: Mapped[str | None] = mapped_column(
        "telefono", String(20), nullable=True
    )
