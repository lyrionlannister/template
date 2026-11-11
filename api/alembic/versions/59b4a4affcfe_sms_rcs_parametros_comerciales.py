"""sms_rcs_parametros_comerciales

Revision ID: 59b4a4affcfe
Revises: 1ec30901ded7
Create Date: 2026-11-11 02:43:01.274712

Semilla de los dos parámetros que faltaban para el precio de venta de
SMS/RCS (ver "SMS y RCS: fórmula pendiente" en /CLAUDE.md): margen objetivo
y mensajes por contacto activo al mes para prorratear el fee de plataforma
de Sent.dm. Confirmado por Luis el 2026-11-11, ambos ajustables después
desde el panel sin nueva migración.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '59b4a4affcfe'
down_revision: Union[str, Sequence[str], None] = '1ec30901ded7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_VIGENTE_DESDE = date(2026, 11, 11)
_FUENTE = "Confirmado por Luis el 2026-11-11"


def upgrade() -> None:
    """Upgrade schema."""
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
                "clave": "sms_rcs_margen_porcentaje",
                "valor": Decimal("0.50"),
                "fuente": _FUENTE,
                "vigente_desde": _VIGENTE_DESDE,
            },
            {
                "public_id": uuid.uuid7(),
                "clave": "sms_rcs_mensajes_por_contacto_mes",
                "valor": Decimal("4"),
                "fuente": _FUENTE,
                "vigente_desde": _VIGENTE_DESDE,
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM parametros_comerciales WHERE clave IN "
        "('sms_rcs_margen_porcentaje', 'sms_rcs_mensajes_por_contacto_mes')"
    )
