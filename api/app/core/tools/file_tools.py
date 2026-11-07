"""Parser multiformato de archivos tabulares para importaciones (CSV/XLSX/
Parquet), centralizado aquí -- no en `contacts/utils/` -- porque cualquier
dominio futuro que importe archivos lo reusa, en vez de duplicarlo por
dominio.

Trata el contenido de CSV/XLSX siempre como datos, nunca como fórmulas ni
como código: este módulo nunca evalúa lo que lee, y `read_tabular` no
sigue rutas ni referencias externas contenidas en el archivo -- solo
extrae su contenido tabular como texto plano.

`neutralize_formulas` queda expuesta aparte para que quien construya el
JSON de variables de un contacto la aplique sobre esos valores -- nunca
sobre el teléfono: un E.164 válido empieza siempre en `+`, que es justo
uno de los caracteres que esta función neutraliza, así que aplicarla sobre
la columna de teléfono de forma automática corrompería todos los
números."""

import io
from typing import Literal

import polars as pl
from fastapi import UploadFile

_FORMULA_START = r"^[=+\-@\t\r]"
_TAMANO_BLOQUE = 1024 * 1024


class ArchivoDemasiadoGrandeError(ValueError):
    """El archivo subido supera el límite de tamaño vigente."""


class FormatoArchivoInvalidoError(ValueError):
    """El contenido del archivo no corresponde a ningún formato soportado."""


async def read_within_limit(archivo: UploadFile, max_bytes: int) -> bytes:
    """Lee el archivo en bloques de 1 MB, cortando antes de bufferear todo
    si supera `max_bytes` -- nunca carga un archivo desproporcionado
    completo en memoria antes de rechazarlo."""

    leido = bytearray()
    while True:
        bloque = await archivo.read(_TAMANO_BLOQUE)
        if not bloque:
            break
        leido.extend(bloque)
        if len(leido) > max_bytes:
            raise ArchivoDemasiadoGrandeError(
                f"El archivo supera el límite de {max_bytes} bytes."
            )
    return bytes(leido)


def neutralize_formulas(df: pl.DataFrame) -> pl.DataFrame:
    """Prefija `'` a toda celda de texto que empiece como fórmula de
    hoja de cálculo, para que un valor importado nunca se ejecute como
    código si el dato se vuelve a abrir en Excel/Sheets más adelante."""

    columnas_texto = [nombre for nombre, tipo in df.schema.items() if tipo == pl.String]
    if not columnas_texto:
        return df
    return df.with_columns(
        [
            pl.when(pl.col(c).str.contains(_FORMULA_START))
            .then(pl.lit("'") + pl.col(c))
            .otherwise(pl.col(c))
            .alias(c)
            for c in columnas_texto
        ]
    )


def tipo_real_coincide(
    content: bytes, formato: Literal["csv", "xlsx", "parquet"]
) -> bool:
    """Sniff liviano del tipo real del archivo contra una extensión que
    puede mentir: XLSX real es un ZIP (firma `PK\\x03\\x04`), Parquet real
    empieza en `PAR1`, y un CSV real es texto plano -- no debería traer
    bytes nulos en su arranque, que es justo lo que delata un binario
    (XLSX/imagen/etc.) renombrado a `.csv`."""

    cabecera = content[:8]
    if formato == "xlsx":
        return cabecera.startswith(b"PK\x03\x04")
    if formato == "parquet":
        return cabecera.startswith(b"PAR1")
    return b"\x00" not in content[:4096]


def _leer_csv(content: bytes) -> pl.DataFrame:
    try:
        texto = content.decode("utf-8")
    except UnicodeDecodeError:
        texto = content.decode("cp1252")
    return pl.read_csv(
        io.StringIO(texto),
        infer_schema_length=0,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )


def read_tabular(
    content: bytes, formato: Literal["csv", "xlsx", "parquet"]
) -> list[dict[str, str]]:
    """Parsea CSV/XLSX/Parquet a una lista de dicts de texto plano. Nunca
    evalúa fórmulas ni sigue referencias externas del archivo -- solo lee
    su contenido tabular como datos. No aplica `neutralize_formulas`: a
    esta altura todavía no se sabe qué columna es el teléfono (eso lo
    decide el mapeo que el usuario confirma después), y neutralizarla por
    error corrompería todo número E.164 válido.

    `formato` es un string plano (no el enum del dominio `contacts`): este
    módulo vive en `core` y no conoce dominios de negocio -- quien lo llama
    pasa `importacion.formato.value` o el string directo."""

    if formato == "csv":
        df = _leer_csv(content)
    elif formato == "xlsx":
        df = pl.read_excel(io.BytesIO(content))
    elif formato == "parquet":
        df = pl.read_parquet(io.BytesIO(content))
    else:
        raise FormatoArchivoInvalidoError(f"Formato no soportado: {formato}")

    df = df.select([pl.col(c).cast(pl.String, strict=False) for c in df.columns])
    return df.to_dicts()
