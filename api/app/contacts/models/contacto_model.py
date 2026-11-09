"""Contacto del tenant, identificado por teléfono E.164 (único por tenant).
`variables` es el JSON libre, propio de cada contacto, sin estructura fija
a nivel de tenant -- cada importación declara su propio mapeo de columnas
(ver `ImportacionContacto.mapeo_variables`) y el upsert hace merge no
destructivo sobre este dict, nunca lo reemplaza entero.

`variables` es `JSONB` (migrado desde `JSON` en la fase de Audiencias,
2026-11-09): `jsonb` habilita el operador de existencia de clave (`?`,
`.has_key()`) sin casts frágiles -- necesario para el constructor de
filtros de Audiencias."""

from typing import Any

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class Contacto(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "contactos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "telefono", name="uq_contactos_tenant_telefono"),
    )

    telefono: Mapped[str] = mapped_column("telefono", String(20), nullable=False)
    variables: Mapped[dict[str, Any]] = mapped_column(
        "variables", JSONB, nullable=False, default=dict
    )
