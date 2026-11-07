"""Importa cada `*_model.py` de cada dominio para que SQLAlchemy registre su
mapeo en `Base.metadata` antes de que Alembic compare el esquema real contra
el declarado (autogenerate) o de correr una migración."""

from app.app_platform.models import costo_canal_model  # noqa: F401
