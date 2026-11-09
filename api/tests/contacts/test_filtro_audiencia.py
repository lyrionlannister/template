"""Validación de `FiltroAudiencia`/`Condicion`: estructura, no texto libre.
Un filtro malformado se rechaza al construirse, nunca llega a ejecutarse
(OWASP: sin inyección posible a través de nombres de clave del JSON)."""

import pytest
from pydantic import ValidationError

from app.contacts.schemas.filtro_schema import Condicion, FiltroAudiencia


def test_condicion_rechaza_campo_no_permitido() -> None:
    with pytest.raises(ValidationError):
        Condicion(field="columna_inventada", op="eq", value="x")


def test_condicion_rechaza_operador_no_permitido_para_el_campo() -> None:
    with pytest.raises(ValidationError):
        Condicion(field="telefono", op="gt", value="1")


@pytest.mark.parametrize(
    "clave_insegura",
    [
        "algo; DROP TABLE contactos;--",
        "algo' OR '1'='1",
        "algo->>'x'",
        "algo.anidado",
        "",
        " ",
    ],
)
def test_condicion_rechaza_clave_de_variable_insegura(clave_insegura: str) -> None:
    with pytest.raises(ValidationError):
        Condicion(field=f"variables.{clave_insegura}", op="eq", value="x")


def test_condicion_acepta_clave_de_variable_segura() -> None:
    condicion = Condicion(field="variables.saldo_actual_2", op="eq", value="100")
    assert condicion.clave_variable == "saldo_actual_2"


def test_condicion_exists_no_acepta_valor() -> None:
    with pytest.raises(ValidationError):
        Condicion(field="variables.ciudad", op="exists", value="CDMX")


def test_condicion_exists_no_requiere_valor() -> None:
    condicion = Condicion(field="variables.ciudad", op="exists")
    assert condicion.value is None


def test_condicion_operador_con_valor_requiere_valor() -> None:
    with pytest.raises(ValidationError):
        Condicion(field="variables.ciudad", op="eq")


def test_filtro_vacio_se_rechaza() -> None:
    with pytest.raises(ValidationError):
        FiltroAudiencia(and_=[])


def test_filtro_se_valida_por_alias_and() -> None:
    filtro = FiltroAudiencia.model_validate(
        {"and": [{"field": "telefono", "op": "contains", "value": "573"}]}
    )
    assert filtro.and_[0].field == "telefono"


def test_filtro_serializa_de_vuelta_con_alias_and() -> None:
    filtro = FiltroAudiencia(
        and_=[Condicion(field="telefono", op="eq", value="+573001112233")]
    )
    serializado = filtro.model_dump(by_alias=True)
    assert "and" in serializado
    assert "and_" not in serializado
