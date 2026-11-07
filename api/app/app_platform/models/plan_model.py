"""Plan comercial de Pulso: editable por el administrador del sistema, leído
siempre en vivo (ningún precio ni límite vive en código, `/CLAUDE.md`).

A diferencia de `CostoCanal`/`TipoCambio`/`ParametroComercial`, un plan no
se versiona por vigencia: es una fila mutable. El histórico de qué costó y
qué límite tenía un plan en el pasado lo da el costo/precio aplicado a cada
consumo cuando ocurrió (`/CLAUDE.md`, «Histórico de costos»), no el plan en
sí — el plan de hoy es siempre el vigente.
"""

from decimal import Decimal

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TimestampMixin


class Plan(Base, IdMixin, TimestampMixin):
    __tablename__ = "planes"

    nombre: Mapped[str] = mapped_column(
        "nombre", String(60), nullable=False, unique=True
    )
    precio_mensual_cop: Mapped[Decimal] = mapped_column(
        "precio_mensual_cop", Numeric(12, 0), nullable=False
    )
    limite_filas_importacion: Mapped[int] = mapped_column(
        "limite_filas_importacion", BigInteger, nullable=False
    )
    mensajes_marketing_incluidos: Mapped[int] = mapped_column(
        "mensajes_marketing_incluidos", BigInteger, nullable=False
    )
    precio_marketing_mensaje_cop: Mapped[Decimal] = mapped_column(
        "precio_marketing_mensaje_cop", Numeric(12, 0), nullable=False
    )
    precio_utility_mensaje_cop: Mapped[Decimal] = mapped_column(
        "precio_utility_mensaje_cop", Numeric(12, 0), nullable=False
    )
    max_usuarios: Mapped[int] = mapped_column(
        "max_usuarios", BigInteger, nullable=False
    )
    max_whatsapp_numeros: Mapped[int] = mapped_column(
        "max_whatsapp_numeros", BigInteger, nullable=False
    )
