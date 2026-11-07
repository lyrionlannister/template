"""Tipo de cambio (TRM) por par de moneda, versionado por vigencia — mismo
patrón que `CostoCanal`. Necesario porque los costos de Meta se guardan en
USD y los precios de Pulso en COP: convertir hoy con la TRM de hoy, nunca
recalcular el pasado con la TRM vigente ahora mismo.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TimestampMixin


class TipoCambio(Base, IdMixin, TimestampMixin):
    __tablename__ = "tipos_cambio"

    par: Mapped[str] = mapped_column("par", String(10), nullable=False, index=True)
    valor: Mapped[Decimal] = mapped_column("valor", Numeric(18, 6), nullable=False)
    fuente: Mapped[str] = mapped_column("fuente", String(200), nullable=False)
    vigente_desde: Mapped[date] = mapped_column("vigente_desde", Date, nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(
        "vigente_hasta", Date, nullable=True
    )
