"""Snapshot de una audiencia estática: un contacto que cumplía el filtro en
el momento de `Audiencia.congelada_en`. Solo se escribe una vez, al crear la
audiencia -- nunca se recalcula ni se actualiza fila por fila."""

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base


class AudienciaContacto(Base):
    __tablename__ = "audiencias_contactos"

    audiencia_id: Mapped[int] = mapped_column(
        "audiencia_id",
        BigInteger,
        ForeignKey("audiencias.id", ondelete="CASCADE"),
        primary_key=True,
    )
    contacto_id: Mapped[int] = mapped_column(
        "contacto_id",
        BigInteger,
        ForeignKey("contactos.id", ondelete="CASCADE"),
        primary_key=True,
    )
