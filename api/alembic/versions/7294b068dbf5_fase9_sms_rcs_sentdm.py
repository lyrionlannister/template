"""fase9_sms_rcs_sentdm

Revision ID: 7294b068dbf5
Revises: 59b4a4affcfe
Create Date: 2026-11-11 03:10:00.000000

Fase 9 (SMS/RCS por Sent.dm): columna de referencia a la plantilla de Sent
en `plantillas`, y semilla de costo/precio para sms y rcs. Costo del
estimador de Sent.dm (pricing-calculator, pestaña "Sent Router", 100%
Colombia), no del piloto pagado verificado -- ver "SMS y RCS: fórmula
pendiente" en /CLAUDE.md. Confirmado por Luis el 2026-11-11, parametrizable
y reemplazable sin nueva migración cuando exista el costo del piloto.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7294b068dbf5'
down_revision: Union[str, Sequence[str], None] = '59b4a4affcfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_VIGENTE_DESDE = date(2026, 11, 11)
_FUENTE_COSTO = (
    "Estimador Sent.dm (pricing-calculator, pestaña Sent Router, 100% "
    "Colombia), pendiente de cotización comercial y piloto pagado -- "
    "confirmado por Luis el 2026-11-11"
)
_FUENTE_PRECIO = (
    "Calculado: (0,0011 USD carrier + 0,0150 USD fee Sent / 4 mensajes por "
    "contacto activo al mes) x 1,5 margen x TRM 3228,26 -- confirmado por "
    "Luis el 2026-11-11"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "plantillas",
        sa.Column("nombre_plantilla_sent", sa.String(length=512), nullable=True),
    )

    costos_canal = sa.table(
        "costos_canal",
        sa.column("public_id", sa.Uuid),
        sa.column("canal", sa.Enum("whatsapp", "sms", "rcs", name="canal_mensajeria")),
        sa.column("proveedor", sa.String),
        sa.column("costo_unitario", sa.Numeric),
        sa.column("moneda", sa.String),
        sa.column("vigente_desde", sa.Date),
        sa.column("fuente", sa.String),
    )
    op.bulk_insert(
        costos_canal,
        [
            {
                "public_id": uuid.uuid7(),
                "canal": "sms",
                "proveedor": "sent",
                "costo_unitario": Decimal("0.0011"),
                "moneda": "USD",
                "vigente_desde": _VIGENTE_DESDE,
                "fuente": _FUENTE_COSTO,
            },
            {
                "public_id": uuid.uuid7(),
                "canal": "rcs",
                "proveedor": "sent",
                "costo_unitario": Decimal("0.0011"),
                "moneda": "USD",
                "vigente_desde": _VIGENTE_DESDE,
                "fuente": _FUENTE_COSTO,
            },
        ],
    )

    parametros_comerciales = sa.table(
        "parametros_comerciales",
        sa.column("public_id", sa.Uuid),
        sa.column("clave", sa.String),
        sa.column("valor", sa.Numeric),
        sa.column("fuente", sa.String),
        sa.column("vigente_desde", sa.Date),
    )
    op.bulk_insert(
        parametros_comerciales,
        [
            {
                "public_id": uuid.uuid7(),
                "clave": "precio_venta_sms_cop",
                "valor": Decimal("23.49"),
                "fuente": _FUENTE_PRECIO,
                "vigente_desde": _VIGENTE_DESDE,
            },
            {
                "public_id": uuid.uuid7(),
                "clave": "precio_venta_rcs_cop",
                "valor": Decimal("23.49"),
                "fuente": _FUENTE_PRECIO,
                "vigente_desde": _VIGENTE_DESDE,
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM parametros_comerciales WHERE clave IN "
        "('precio_venta_sms_cop', 'precio_venta_rcs_cop')"
    )
    op.execute("DELETE FROM costos_canal WHERE proveedor = 'sent'")
    op.drop_column("plantillas", "nombre_plantilla_sent")
