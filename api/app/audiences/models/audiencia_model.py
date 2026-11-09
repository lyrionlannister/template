"""Audiencia: filtro guardado sobre contactos (ver `SPEC-audiencias.md`).
`filtro` guarda siempre la forma validada por `FiltroAudiencia`
(`app.contacts.schemas.filtro_schema`) -- nunca texto libre.

Dinámica: `filtro` es la fuente de verdad, se resuelve en cada consulta vía
`ContactsService`. Estática: además de `filtro` (se conserva por trazabilidad
y para "duplicar como dinámica"), la lista de contactos queda congelada en
`AudienciaContacto` al crearse, marcada con `congelada_en`."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.audiences.enums.audiences_enums import TipoAudiencia
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class Audiencia(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "audiencias"

    nombre: Mapped[str] = mapped_column("nombre", String(150), nullable=False)
    tipo: Mapped[TipoAudiencia] = mapped_column(
        "tipo", Enum(TipoAudiencia, name="tipo_audiencia"), nullable=False
    )
    filtro: Mapped[dict[str, Any]] = mapped_column("filtro", JSONB, nullable=False)
    congelada_en: Mapped[datetime | None] = mapped_column(
        "congelada_en", DateTime(timezone=True), nullable=True
    )
