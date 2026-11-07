"""Parámetro comercial de valor único, versionado por vigencia — mismo
patrón que `CostoCanal`/`TipoCambio`. Cubre cualquier cifra comercial de
Pulso que no encaje en una tabla propia: días de trial, mensajes gratis de
trial, precio de onboarding, comisión de Wompi. Nunca una constante en
código.

Claves vigentes hoy (ver la semilla en la migración): `trial_dias`,
`trial_mensajes_gratis`, `onboarding_precio_cop`, `comision_wompi_porcentaje`,
`comision_wompi_fijo_cop`, `comision_wompi_iva_porcentaje`,
`impago_reintentos_max`, `impago_dias_entre_reintentos`.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TimestampMixin


class ParametroComercial(Base, IdMixin, TimestampMixin):
    __tablename__ = "parametros_comerciales"

    clave: Mapped[str] = mapped_column("clave", String(60), nullable=False, index=True)
    valor: Mapped[Decimal] = mapped_column("valor", Numeric(18, 6), nullable=False)
    fuente: Mapped[str] = mapped_column("fuente", String(200), nullable=False)
    vigente_desde: Mapped[date] = mapped_column("vigente_desde", Date, nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(
        "vigente_hasta", Date, nullable=True
    )
