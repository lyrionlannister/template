"""Schema base de Pydantic: alias en camelCase para el JSON (lo que recibe y
lee `client/`), snake_case en Python (el vocabulario del resto del backend).
Todo schema de request/response de cualquier dominio hereda de este."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
