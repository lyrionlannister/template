"""Suscripción mensual del tenant. `monto_cop` guarda el valor realmente
cobrado en el último ciclo (precio del plan en ese momento, nunca una
constante) — igual que cualquier consumo en Pulso, el histórico de qué se
cobró lo da el movimiento, no releer el plan de hoy."""

from datetime import date

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.billing.enums.billing_enums import EstadoSuscripcion
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class Suscripcion(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "suscripciones"

    fuente_de_pago_id: Mapped[int | None] = mapped_column(
        "fuente_de_pago_id",
        BigInteger,
        ForeignKey("fuentes_de_pago.id"),
        nullable=True,
    )
    estado: Mapped[EstadoSuscripcion] = mapped_column(
        "estado", Enum(EstadoSuscripcion, name="estado_suscripcion"), nullable=False
    )
    monto_cop: Mapped[Numeric] = mapped_column(
        "monto_cop", Numeric(12, 0), nullable=False
    )
    proxima_fecha_cobro: Mapped[date] = mapped_column(
        "proxima_fecha_cobro", Date, nullable=False
    )
    intentos_fallidos_consecutivos: Mapped[int] = mapped_column(
        "intentos_fallidos_consecutivos", BigInteger, nullable=False, default=0
    )
    ultima_referencia_transaccion: Mapped[str | None] = mapped_column(
        "ultima_referencia_transaccion", String(100), nullable=True
    )
