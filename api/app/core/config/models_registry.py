"""Importa cada `*_model.py` de cada dominio para que SQLAlchemy registre su
mapeo en `Base.metadata` antes de que Alembic compare el esquema real contra
el declarado (autogenerate) o de correr una migración."""

from app.app_platform.models import (  # noqa: F401
    costo_canal_model,
    parametro_comercial_model,
    plan_model,
    tipo_cambio_model,
)
from app.audiences.models import (  # noqa: F401
    audiencia_contacto_model,
    audiencia_model,
)
from app.auth.models import codigo_otp_model, tenant_model, usuario_model  # noqa: F401
from app.billing.models import (  # noqa: F401
    cobro_model,
    evento_pago_procesado_model,
    fuente_de_pago_model,
    movimiento_saldo_model,
    suscripcion_model,
)
from app.contacts.models import (  # noqa: F401
    configuracion_contactos_model,
    conflicto_variable_model,
    contacto_model,
    contacto_rechazado_model,
    importacion_contacto_model,
)
from app.messaging.models import (  # noqa: F401
    conexion_whatsapp_model,
    plantilla_otp_plataforma_model,
)
from app.templates.models import plantilla_model  # noqa: F401
