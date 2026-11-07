"""Movimiento de saldo utilizable del tenant. Esta fase solo genera
movimientos de `recarga`; `consumo` y `ajuste` llegan en fases posteriores
(mensajería/campañas y correcciones manuales auditadas). `referencia` es la
clave de idempotencia propia que se manda a la pasarela antes de intentar
el cobro (ver `money-precision`)."""

from sqlalchemy import Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.billing.enums.billing_enums import (
    ConceptoMovimientoSaldo,
    EstadoTransaccionPago,
    MedioRecarga,
)
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class MovimientoSaldo(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "movimientos_saldo"

    concepto: Mapped[ConceptoMovimientoSaldo] = mapped_column(
        "concepto",
        Enum(ConceptoMovimientoSaldo, name="concepto_movimiento_saldo"),
        nullable=False,
    )
    medio: Mapped[MedioRecarga | None] = mapped_column(
        "medio", Enum(MedioRecarga, name="medio_recarga"), nullable=True
    )
    monto_cop: Mapped[Numeric] = mapped_column(
        "monto_cop", Numeric(12, 0), nullable=False
    )
    estado: Mapped[EstadoTransaccionPago] = mapped_column(
        "estado",
        Enum(EstadoTransaccionPago, name="estado_transaccion_pago"),
        nullable=False,
    )
    referencia: Mapped[str] = mapped_column(
        "referencia", String(100), nullable=False, unique=True
    )
    id_externo_transaccion: Mapped[str | None] = mapped_column(
        "id_externo_transaccion", String(100), nullable=True
    )
