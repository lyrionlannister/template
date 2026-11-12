"""Plantilla de mensaje: el texto (con placeholders `{{variable}}`) que una
campaña envía por un canal. `variables` se extrae de `contenido` al guardar
(`TemplatesService._extraer_variables`), nunca se declara aparte -- una sola
fuente de verdad, ver `SPEC-plantillas.md`.

`categoria`/`nombre_plantilla_meta` solo aplican a WhatsApp: sin ellas no
se puede enviar por Meta Cloud API (la categoría decide precio y consumo
del pool de incluidos) ni referenciar la plantilla aprobada en la cuenta
del cliente. SMS/RCS los dejan en `None`.

`nombre_plantilla_sent` solo aplica a SMS/RCS: referencia a la plantilla
creada y aprobada en el dashboard de Sent.dm (fase 9) -- Sent exige una
plantilla para el primer contacto con alguien que nunca respondió, el
texto libre no sirve para eso. WhatsApp la deja en `None`."""

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.app_platform.enums.costo_canal_enums import CanalMensajeria, CategoriaMensaje
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class Plantilla(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "plantillas"

    nombre: Mapped[str] = mapped_column("nombre", String(150), nullable=False)
    canal: Mapped[CanalMensajeria] = mapped_column(
        "canal", Enum(CanalMensajeria, name="canal_mensajeria"), nullable=False
    )
    contenido: Mapped[str] = mapped_column("contenido", Text, nullable=False)
    variables: Mapped[list[str]] = mapped_column(
        "variables", JSONB, nullable=False, default=list
    )
    categoria: Mapped[CategoriaMensaje | None] = mapped_column(
        "categoria",
        Enum(CategoriaMensaje, name="categoria_mensaje"),
        nullable=True,
    )
    nombre_plantilla_meta: Mapped[str | None] = mapped_column(
        "nombre_plantilla_meta", String(512), nullable=True
    )
    nombre_plantilla_sent: Mapped[str | None] = mapped_column(
        "nombre_plantilla_sent", String(512), nullable=True
    )
