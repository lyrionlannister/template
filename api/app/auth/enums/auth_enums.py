"""Enumeraciones del dominio auth: estado de tenant, rol de usuario y canal
de envío del OTP de inicio de sesión."""

import enum


class EstadoTenant(enum.StrEnum):
    trial = "trial"
    activo = "activo"
    suspendido = "suspendido"


class RolUsuario(enum.StrEnum):
    administrador = "administrador"
    miembro = "miembro"


class CanalOtp(enum.StrEnum):
    whatsapp = "whatsapp"
    sms = "sms"
