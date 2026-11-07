"""Tenant: organización cliente de Pulso, raíz de aislamiento. No hereda
`TenantScopedMixin`: es él mismo la raíz,
no un dato que pertenezca a un tenant.

`plan_id` referencia `planes.id` (dominio `app_platform`) solo por nombre de
tabla, sin importar el modelo `Plan` — no cruza dominios en Python, igual
que cualquier FK entre dominios. Nullable: hasta que exista billing
(Prompt 12) un tenant puede no tener plan asignado todavía, aunque
`AuthService.registrar` ya asigna el plan Esencial por defecto al crear el
tenant.

`onboarding_pagado_en` (fase 5, billing): `None` hasta que el webhook de la
pasarela confirma el cobro único de onboarding. `billing` nunca escribe esta
columna directo (no importa `auth.models`): lo hace a través de
`AuthService.marcar_onboarding_pagado`.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.enums.auth_enums import EstadoTenant
from app.core.database.base import Base, IdMixin, TimestampMixin


class Tenant(Base, IdMixin, TimestampMixin):
    __tablename__ = "tenants"

    nombre: Mapped[str] = mapped_column("nombre", String(200), nullable=False)
    estado: Mapped[EstadoTenant] = mapped_column(
        "estado", Enum(EstadoTenant, name="estado_tenant"), nullable=False
    )
    trial_fin: Mapped[datetime] = mapped_column(
        "trial_fin", DateTime(timezone=True), nullable=False
    )
    plan_id: Mapped[int | None] = mapped_column(
        "plan_id", BigInteger, ForeignKey("planes.id"), nullable=True
    )
    onboarding_pagado_en: Mapped[datetime | None] = mapped_column(
        "onboarding_pagado_en", DateTime(timezone=True), nullable=True
    )
