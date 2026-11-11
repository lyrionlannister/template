"""Conexión de WhatsApp de un tenant, resultado de Embedded Signup: el
número que el tenant conectó con su propia cuenta de WhatsApp Business, y
el token de acceso de Meta para enviar en su nombre -- cifrado en reposo,
nunca en claro (ver `app.core.security.credenciales_cipher`).

`phone_number_id` es único GLOBAL (Meta lo asigna único en toda la
plataforma, no por tenant): la constraint sin `tenant_id` es intencional,
así se detecta que un número ya fue reclamado por otro tenant."""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class ConexionWhatsapp(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "conexiones_whatsapp"
    __table_args__ = (
        UniqueConstraint(
            "phone_number_id", name="uq_conexiones_whatsapp_phone_number_id"
        ),
    )

    waba_id: Mapped[str] = mapped_column("waba_id", String(50), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(
        "phone_number_id", String(50), nullable=False
    )
    numero_telefono: Mapped[str] = mapped_column(
        "numero_telefono", String(20), nullable=False
    )
    token_acceso_cifrado: Mapped[str] = mapped_column(
        "token_acceso_cifrado", Text, nullable=False
    )
