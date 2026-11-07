"""Costo de proveedor por canal y categoría, versionado por vigencia.

No es un dato de tenant: pertenece a la plataforma (no hereda
`TenantScopedMixin`). Nunca se actualiza ni se borra un registro histórico:
registrar un costo nuevo cierra la vigencia del anterior (ver
`CostoCanalService.registrar_costo`). `vigente_hasta` en `NULL` significa
"vigente hasta hoy, sin cierre todavía" — nunca hay más de un registro
abierto (`vigente_hasta IS NULL`) por combinación de canal y categoría.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.core.database.base import Base, IdMixin, TimestampMixin


class CostoCanal(Base, IdMixin, TimestampMixin):
    __tablename__ = "costos_canal"

    canal: Mapped[CanalMensajeria] = mapped_column(
        "canal", Enum(CanalMensajeria, name="canal_mensajeria"), nullable=False
    )
    categoria: Mapped[CategoriaMensaje | None] = mapped_column(
        "categoria", Enum(CategoriaMensaje, name="categoria_mensaje"), nullable=True
    )
    proveedor: Mapped[str] = mapped_column("proveedor", String(60), nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(
        "costo_unitario", Numeric(12, 4), nullable=False
    )
    moneda: Mapped[str] = mapped_column("moneda", String(3), nullable=False)
    vigente_desde: Mapped[date] = mapped_column("vigente_desde", Date, nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(
        "vigente_hasta", Date, nullable=True
    )
    fuente: Mapped[str] = mapped_column("fuente", String(200), nullable=False)
