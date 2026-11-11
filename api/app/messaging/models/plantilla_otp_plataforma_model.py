"""Plantilla de autenticación de WhatsApp que usa la PLATAFORMA para
enviar el OTP de login -- nunca una plantilla de ningún tenant. No es
tenant-scoped (mismo patrón que `Plan`): es una identidad de plataforma,
creada desde el panel de administrador del sistema, con su estado de
aprobación en Meta (`PENDING`/`APPROVED`/`REJECTED`)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TimestampMixin


class PlantillaOtpPlataforma(Base, IdMixin, TimestampMixin):
    __tablename__ = "plantillas_otp_plataforma"

    nombre: Mapped[str] = mapped_column("nombre", String(512), nullable=False)
    idioma: Mapped[str] = mapped_column("idioma", String(10), nullable=False)
    estado_meta: Mapped[str] = mapped_column(
        "estado_meta", String(20), nullable=False, default="PENDING"
    )
    meta_template_id: Mapped[str | None] = mapped_column(
        "meta_template_id", String(60), nullable=True
    )
