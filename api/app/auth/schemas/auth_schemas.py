"""Schemas de request/response de auth. Ninguno lleva `access_token` ni
`refresh_token`: esos solo viajan en cookies httpOnly."""

from uuid import UUID

from pydantic import EmailStr, field_validator

from app.auth.enums.auth_enums import CanalOtp, RolUsuario
from app.core.schemas.base_schema import BaseSchema
from app.core.security.password_policy import validar_fortaleza_password


class RegistroRequest(BaseSchema):
    nombre_organizacion: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        return validar_fortaleza_password(valor)


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseSchema):
    id_token: str


class OlvidePasswordRequest(BaseSchema):
    email: EmailStr


class RestablecerPasswordRequest(BaseSchema):
    token: str
    nueva_password: str

    @field_validator("nueva_password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        return validar_fortaleza_password(valor)


class InvitarUsuarioRequest(BaseSchema):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        return validar_fortaleza_password(valor)


class OtpEnviarRequest(BaseSchema):
    canal: CanalOtp


class OtpVerificarRequest(BaseSchema):
    codigo: str
    canal: CanalOtp


class UsuarioRespuesta(BaseSchema):
    public_id: UUID
    email: str
    rol: RolUsuario
    mfa_habilitado: bool
