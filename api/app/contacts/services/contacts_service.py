"""Lógica de negocio de contactos: previsualización e importación de
archivos CSV/XLSX/Parquet (ver `resources/specs/SPEC-contactos.md`)."""

import json
import uuid
from dataclasses import dataclass
from datetime import date

from fastapi import UploadFile

from app.app_platform.exceptions import (
    LimiteDePlanError,
    ParametroComercialFaltanteError,
)
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.auth.services.auth_service import AuthService
from app.contacts.exceptions import (
    FormatoArchivoNoSoportadoError,
    LimiteDeFilasExcedidoError,
    TipoDeArchivoNoCoincideError,
)
from app.core.tools.file_tools import (
    read_tabular,
    read_within_limit,
    tipo_real_coincide,
)
from app.core.valkey.client import valkey_client

_CLAVE_IMPORTACION_TAMANO_MAXIMO_MB = "importacion_tamano_maximo_mb"
_PREVIEW_TTL_SEGUNDOS = 30 * 60
_MUESTRA_FILAS = 20
_EXTENSIONES_SOPORTADAS = {"csv": "csv", "xlsx": "xlsx", "parquet": "parquet"}


@dataclass
class ResultadoPrevisualizacion:
    preview_id: str
    columnas: list[str]
    muestra: list[dict[str, str]]
    total_filas: int


class ContactsService:
    def __init__(
        self,
        auth_service: AuthService,
        plan_service: PlanService,
        parametro_comercial_service: ParametroComercialService,
    ):
        self.auth_service = auth_service
        self.plan_service = plan_service
        self.parametro_comercial_service = parametro_comercial_service

    async def previsualizar(
        self, tenant_id: int, archivo: UploadFile
    ) -> ResultadoPrevisualizacion:
        formato = self._formato_desde_nombre(archivo.filename)
        max_bytes = await self._tamano_maximo_bytes()

        content = await read_within_limit(archivo, max_bytes)
        if not tipo_real_coincide(content, formato):
            raise TipoDeArchivoNoCoincideError(
                "El contenido del archivo no corresponde a su extensión."
            )

        filas = read_tabular(content, formato)
        total_filas = len(filas)

        limite_filas = await self._limite_filas_del_tenant(tenant_id)
        if total_filas > limite_filas:
            raise LimiteDeFilasExcedidoError(
                f"El archivo tiene {total_filas} filas; el plan vigente de "
                f"esta organización permite hasta {limite_filas}."
            )

        columnas = list(filas[0].keys()) if filas else []
        preview_id = uuid.uuid4().hex
        await valkey_client.set(
            self._clave_preview(tenant_id, preview_id),
            json.dumps({"formato": formato, "columnas": columnas, "filas": filas}),
            ex=_PREVIEW_TTL_SEGUNDOS,
        )

        return ResultadoPrevisualizacion(
            preview_id=preview_id,
            columnas=columnas,
            muestra=filas[:_MUESTRA_FILAS],
            total_filas=total_filas,
        )

    async def _tamano_maximo_bytes(self) -> int:
        valor_mb = await self.parametro_comercial_service.valor_vigente(
            _CLAVE_IMPORTACION_TAMANO_MAXIMO_MB, date.today()
        )
        if valor_mb is None:
            raise ParametroComercialFaltanteError(
                f"Falta el parámetro comercial "
                f"'{_CLAVE_IMPORTACION_TAMANO_MAXIMO_MB}'."
            )
        return int(valor_mb * 1024 * 1024)

    async def _limite_filas_del_tenant(self, tenant_id: int) -> int:
        tenant = await self.auth_service.obtener_tenant(tenant_id)
        if tenant is None or tenant.plan_id is None:
            raise LimiteDePlanError(
                "Esta organización no tiene un plan asignado todavía."
            )
        plan = await self.plan_service.obtener(tenant.plan_id)
        if plan is None:
            raise LimiteDePlanError(
                "El plan asignado a esta organización ya no existe."
            )
        return plan.limite_filas_importacion

    @staticmethod
    def _formato_desde_nombre(nombre_archivo: str | None) -> str:
        if not nombre_archivo or "." not in nombre_archivo:
            raise FormatoArchivoNoSoportadoError(
                "El archivo no tiene una extensión reconocible."
            )
        extension = nombre_archivo.rsplit(".", 1)[-1].lower()
        formato = _EXTENSIONES_SOPORTADAS.get(extension)
        if formato is None:
            raise FormatoArchivoNoSoportadoError(
                f"Formato no soportado: .{extension}. Solo CSV, XLSX y Parquet."
            )
        return formato

    @staticmethod
    def _clave_preview(tenant_id: int, preview_id: str) -> str:
        return f"importacion:preview:{tenant_id}:{preview_id}"
