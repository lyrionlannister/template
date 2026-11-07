"""Log de idempotencia de eventos de pago entrantes (webhooks). Deliberadamente
sin `TenantScopedMixin`: un evento llega antes de poder resolverse siempre a
un tenant (la referencia puede no mapear a nada conocido todavía), así que
`tenant_id` es nullable y se llena cuando el handler logra identificar al
tenant dueño de la transacción. La unicidad de `(pasarela, id_evento_externo)`
es la que de verdad impide procesar el mismo evento dos veces — el chequeo
en el service es una segunda capa, no la única."""

from typing import Any

from sqlalchemy import JSON, BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, IdMixin, TimestampMixin


class EventoPagoProcesado(Base, IdMixin, TimestampMixin):
    __tablename__ = "eventos_pago_procesados"
    __table_args__ = (
        UniqueConstraint(
            "pasarela", "id_evento_externo", name="uq_eventos_pago_procesados_evento"
        ),
    )

    tenant_id: Mapped[int | None] = mapped_column(
        "tenant_id", BigInteger, index=True, nullable=True
    )
    pasarela: Mapped[str] = mapped_column("pasarela", String(30), nullable=False)
    id_evento_externo: Mapped[str] = mapped_column(
        "id_evento_externo", String(150), nullable=False
    )
    evento: Mapped[str] = mapped_column("evento", String(60), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column("payload", JSON, nullable=False)
