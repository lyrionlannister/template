"""Base declarativa y convenciones de modelos, compartidas por todo dominio.

Convenciones del proyecto (únicas, no se repiten por dominio):

- Identificadores: dos columnas, no una. `id` es `BigInteger` autoincremental,
  primary key real: el PK que usan los joins y las FK internas, rápido y
  compacto. `public_id` es un `UUID` generado en Python con `uuid.uuid7()`
  (stdlib desde Python 3.14, ordenable por tiempo de creación): es el único
  identificador que sale de la base de datos — a la API, a una URL, a un log.
  `id` nunca se expone: es secuencial y dejaría ver volumen de negocio y
  permitiría enumerar registros (OWASP: referencia directa a objeto insegura).
- Marcas de tiempo: `creado_en` y `actualizado_en`, siempre `DateTime(timezone=True)`,
  con default y onupdate en servidor (`func.now()`). Un `UPDATE` que no pase por
  el ORM (SQL crudo, `bulk_update_mappings`) no dispara `onupdate`: quien lo use
  debe setear `actualizado_en` a mano.
- Atributos: todo atributo mapeado de un modelo va en español, con el nombre de
  columna físico fijado explícito vía `name="..."` (no se deja a la inferencia
  automática de SQLAlchemy a partir del nombre del atributo Python).
- Nombres de tabla: snake_case, plural, explícito en cada modelo vía
  `__tablename__` (sin pluralización automática: es más simple y no falla con
  plurales irregulares).
- Nombres de restricciones: siguen `NAMING_CONVENTION` de abajo, para que Alembic
  autogenere nombres estables (`ix_`, `uq_`, `ck_`, `fk_`, `pk_`) en vez de los
  nombres ad-hoc que genera PostgreSQL por defecto.
- Aislamiento por tenant: todo modelo de datos de un tenant hereda
  `TenantScopedMixin`, que agrega la columna `tenant_id`. La FK hacia la tabla
  `tenants` (dominio `auth`) se agrega cuando esa tabla exista; hasta entonces
  la columna solo lleva índice. El filtrado por tenant no lo aplica el modelo:
  lo aplica `TenantScopedRepository` (ver `tenant_repository.py`).
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    creado_en: Mapped[datetime] = mapped_column(
        "creado_en", DateTime(timezone=True), server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        "actualizado_en",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TenantScopedMixin:
    """Marca un modelo como propiedad de un tenant.

    `TenantScopedRepository` es quien lee esta columna para filtrar; el mixin
    solo declara el dato, no aplica ninguna regla por sí mismo.
    """

    tenant_id: Mapped[int] = mapped_column(
        "tenant_id", BigInteger, index=True, nullable=False
    )


class IdMixin:
    id: Mapped[int] = mapped_column(
        "id", BigInteger, primary_key=True, autoincrement=True
    )
    public_id: Mapped[uuid.UUID] = mapped_column(
        "public_id", default=uuid.uuid7, unique=True, index=True, nullable=False
    )
