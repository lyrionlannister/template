"""Auditoría de cada conflicto real de fusión de variables (valor
existente no vacío vs. valor nuevo no vacío y distinto), sin importar la
política activa -- así el tenant siempre puede revisar qué cambió y
revertir un campo puntual si una importación se equivocó."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class ConflictoVariableContacto(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "conflictos_variable_contacto"

    contacto_id: Mapped[int] = mapped_column(
        "contacto_id",
        BigInteger,
        ForeignKey("contactos.id"),
        nullable=False,
        index=True,
    )
    importacion_id: Mapped[int] = mapped_column(
        "importacion_id",
        BigInteger,
        ForeignKey("importaciones_contacto.id"),
        nullable=False,
        index=True,
    )
    clave: Mapped[str] = mapped_column("clave", String(120), nullable=False)
    valor_anterior: Mapped[str] = mapped_column(
        "valor_anterior", String(2000), nullable=False
    )
    valor_nuevo: Mapped[str] = mapped_column(
        "valor_nuevo", String(2000), nullable=False
    )
    revertido_en: Mapped[datetime | None] = mapped_column(
        "revertido_en", DateTime(timezone=True), nullable=True
    )
