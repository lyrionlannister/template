"""Una tarea de importación de contactos. Guarda el mapeo que el usuario
confirmó (qué columna es el teléfono, qué columnas son variables y con qué
nombre) para que el `BackgroundTask` lo use sin depender de que Valkey siga
teniendo la previsualización -- la clave de Valkey se borra al confirmar."""

from sqlalchemy import JSON, BigInteger, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.contacts.enums.contacts_enums import (
    EstadoImportacion,
    FormatoArchivoImportacion,
)
from app.core.database.base import Base, IdMixin, TenantScopedMixin, TimestampMixin


class ImportacionContacto(Base, IdMixin, TenantScopedMixin, TimestampMixin):
    __tablename__ = "importaciones_contacto"

    nombre_archivo: Mapped[str] = mapped_column(
        "nombre_archivo", String(255), nullable=False
    )
    formato: Mapped[FormatoArchivoImportacion] = mapped_column(
        "formato",
        Enum(FormatoArchivoImportacion, name="formato_archivo_importacion"),
        nullable=False,
    )
    estado: Mapped[EstadoImportacion] = mapped_column(
        "estado",
        Enum(EstadoImportacion, name="estado_importacion"),
        nullable=False,
        default=EstadoImportacion.pendiente,
    )
    columna_telefono: Mapped[str] = mapped_column(
        "columna_telefono", String(120), nullable=False
    )
    mapeo_variables: Mapped[dict[str, str]] = mapped_column(
        "mapeo_variables", JSON, nullable=False
    )
    total_filas: Mapped[int] = mapped_column(
        "total_filas", BigInteger, nullable=False, default=0
    )
    filas_aceptadas: Mapped[int] = mapped_column(
        "filas_aceptadas", BigInteger, nullable=False, default=0
    )
    filas_rechazadas: Mapped[int] = mapped_column(
        "filas_rechazadas", BigInteger, nullable=False, default=0
    )
    filas_con_advertencia: Mapped[int] = mapped_column(
        "filas_con_advertencia", BigInteger, nullable=False, default=0
    )
    motivo_fallo: Mapped[str | None] = mapped_column(
        "motivo_fallo", String(500), nullable=True
    )
