"""Fila rechazada de una importación, con su motivo exacto -- es el informe
de rechazos consultable desde el panel. Sin FK a `Contacto`: una fila
rechazada nunca llegó a crear ni a tocar un contacto."""

from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class ContactoRechazado(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "contactos_rechazados"

    importacion_id: Mapped[int] = mapped_column(
        "importacion_id",
        BigInteger,
        ForeignKey("importaciones_contacto.id"),
        nullable=False,
        index=True,
    )
    fila_cruda: Mapped[dict[str, Any]] = mapped_column(
        "fila_cruda", JSON, nullable=False
    )
    motivo: Mapped[str] = mapped_column("motivo", String(300), nullable=False)
