"""Tests del parser compartido de archivos tabulares
(`core/tools/file_tools.py`): un formato por caso, encoding LatAm,
neutralización de fórmulas y corte por tamaño sin bufferear todo."""

import io

import openpyxl
import polars as pl
import pytest

from app.core.tools.file_tools import (
    ArchivoDemasiadoGrandeError,
    neutralize_formulas,
    read_tabular,
    read_within_limit,
    tipo_real_coincide,
)


class _ArchivoFalso:
    """Stub mínimo de `UploadFile` para probar `read_within_limit` sin
    levantar FastAPI: solo necesita un `.read(n)` asíncrono."""

    def __init__(self, contenido: bytes) -> None:
        self._buffer = io.BytesIO(contenido)

    async def read(self, size: int) -> bytes:
        return self._buffer.read(size)


def test_read_tabular_csv() -> None:
    contenido = b"telefono,nombre\n+573001112233,Ana\n"
    filas = read_tabular(contenido, "csv")
    assert filas == [{"telefono": "+573001112233", "nombre": "Ana"}]


def test_read_tabular_csv_encoding_latam() -> None:
    contenido = "telefono,nombre\n+573001112233,Peña\n".encode("cp1252")
    filas = read_tabular(contenido, "csv")
    assert filas == [{"telefono": "+573001112233", "nombre": "Peña"}]


def test_read_tabular_xlsx() -> None:
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(["telefono", "nombre"])
    hoja.append(["+573001112233", "Ana"])
    buffer = io.BytesIO()
    libro.save(buffer)
    filas = read_tabular(buffer.getvalue(), "xlsx")
    assert filas == [{"telefono": "+573001112233", "nombre": "Ana"}]


def test_read_tabular_parquet() -> None:
    df = pl.DataFrame({"telefono": ["+573001112233"], "nombre": ["Ana"]})
    buffer = io.BytesIO()
    df.write_parquet(buffer)
    filas = read_tabular(buffer.getvalue(), "parquet")
    assert filas == [{"telefono": "+573001112233", "nombre": "Ana"}]


def test_read_tabular_no_corrompe_telefono_e164() -> None:
    """Regresión: `read_tabular` no debe aplicar `neutralize_formulas` por
    su cuenta -- un E.164 válido empieza en `+`, uno de los caracteres que
    esa función neutraliza, y corromperlo aquí perdería el dato."""
    contenido = b"telefono,nombre\n+573001112233,=cmd|'/c calc'!A1\n"
    filas = read_tabular(contenido, "csv")
    assert filas[0]["telefono"] == "+573001112233"
    assert filas[0]["nombre"] == "=cmd|'/c calc'!A1"


def test_neutralize_formulas_no_toca_texto_normal() -> None:
    df = pl.DataFrame({"nombre": ["Ana", "=HACK()"]})
    resultado = neutralize_formulas(df)
    assert resultado["nombre"].to_list() == ["Ana", "'=HACK()"]


async def test_read_within_limit_corta_sin_bufferear_todo() -> None:
    archivo = _ArchivoFalso(b"a" * (5 * 1024 * 1024))
    with pytest.raises(ArchivoDemasiadoGrandeError):
        await read_within_limit(archivo, max_bytes=1024 * 1024)


async def test_read_within_limit_acepta_en_el_limite() -> None:
    contenido = b"a" * 1024
    archivo = _ArchivoFalso(contenido)
    resultado = await read_within_limit(archivo, max_bytes=1024)
    assert resultado == contenido


def test_tipo_real_coincide_csv_real() -> None:
    assert tipo_real_coincide(b"telefono,nombre\n+573001112233,Ana\n", "csv")


def test_tipo_real_coincide_rechaza_xlsx_renombrado_a_csv() -> None:
    libro = openpyxl.Workbook()
    libro.active.append(["telefono"])
    buffer = io.BytesIO()
    libro.save(buffer)
    assert not tipo_real_coincide(buffer.getvalue(), "csv")


def test_tipo_real_coincide_xlsx_real() -> None:
    libro = openpyxl.Workbook()
    libro.active.append(["telefono"])
    buffer = io.BytesIO()
    libro.save(buffer)
    assert tipo_real_coincide(buffer.getvalue(), "xlsx")


def test_tipo_real_coincide_rechaza_csv_renombrado_a_xlsx() -> None:
    assert not tipo_real_coincide(b"telefono,nombre\n+57300,Ana\n", "xlsx")


def test_tipo_real_coincide_parquet_real() -> None:
    df = pl.DataFrame({"telefono": ["+573001112233"]})
    buffer = io.BytesIO()
    df.write_parquet(buffer)
    assert tipo_real_coincide(buffer.getvalue(), "parquet")
