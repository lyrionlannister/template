"""Código de un solo uso (OTP) para la verificación MFA del login. El
código nunca se guarda en claro: `codigo_hash` es el HMAC de
`core/security/otp_hash.py`.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.enums.auth_enums import CanalOtp
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class CodigoOtp(Base, TenantScopedMixin, IdMixin, TimestampMixin):
    __tablename__ = "codigos_otp"
    __table_args__ = (ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),)

    usuario_id: Mapped[int] = mapped_column(
        "usuario_id",
        BigInteger,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canal: Mapped[CanalOtp] = mapped_column(
        "canal", Enum(CanalOtp, name="canal_otp"), nullable=False
    )
    codigo_hash: Mapped[str] = mapped_column(
        "codigo_hash", String(64), nullable=False, index=True
    )
    expira_en: Mapped[datetime] = mapped_column(
        "expira_en", DateTime(timezone=True), nullable=False
    )
    consumido_en: Mapped[datetime | None] = mapped_column(
        "consumido_en", DateTime(timezone=True), nullable=True
    )
