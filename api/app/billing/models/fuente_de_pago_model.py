"""Fuente de pago tokenizada de un tenant (tarjeta o Nequi), guardada en la
pasarela, no en Pulso: aquí solo vive el identificador que la pasarela
entrega (`id_externo`) y su estado, nunca el número de tarjeta ni el PIN de
Nequi. `es_recurrente` distingue una fuente creada con preautorización
(permite cobro recurrente sin 3DS, ver `SuscripcionService`) de una creada
para un cobro simple (onboarding, recarga puntual)."""

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.billing.enums.billing_enums import EstadoFuenteDePago, TipoFuenteDePago
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class FuenteDePago(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "fuentes_de_pago"

    tipo: Mapped[TipoFuenteDePago] = mapped_column(
        "tipo", Enum(TipoFuenteDePago, name="tipo_fuente_de_pago"), nullable=False
    )
    pasarela: Mapped[str] = mapped_column("pasarela", String(30), nullable=False)
    id_externo: Mapped[str] = mapped_column("id_externo", String(100), nullable=False)
    estado: Mapped[EstadoFuenteDePago] = mapped_column(
        "estado",
        Enum(EstadoFuenteDePago, name="estado_fuente_de_pago"),
        nullable=False,
    )
    es_recurrente: Mapped[bool] = mapped_column(
        "es_recurrente", Boolean, nullable=False, default=False
    )
    descripcion: Mapped[str | None] = mapped_column(
        "descripcion", String(60), nullable=True
    )
