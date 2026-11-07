"""Cargo que no es un movimiento de saldo: onboarding (pago único) y cada
ciclo de la suscripción mensual. Se persiste con `estado=pendiente` ANTES de
llamar a la pasarela (ver `money-precision`): si el proceso muere entre la
llamada y la respuesta, el registro ya existe y se puede reconciliar
consultando la pasarela por `referencia`, en vez de perder el intento o
reintentarlo a ciegas. Solo el webhook (pasarela, validado) mueve el estado
a `aprobada`/`rechazada`/`error`."""

from sqlalchemy import BigInteger, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.billing.enums.billing_enums import ConceptoCobro, EstadoTransaccionPago
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class Cobro(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "cobros"

    concepto: Mapped[ConceptoCobro] = mapped_column(
        "concepto", Enum(ConceptoCobro, name="concepto_cobro"), nullable=False
    )
    fuente_de_pago_id: Mapped[int | None] = mapped_column(
        "fuente_de_pago_id",
        BigInteger,
        ForeignKey("fuentes_de_pago.id"),
        nullable=True,
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
