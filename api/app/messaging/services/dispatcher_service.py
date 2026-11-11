"""Tabla de enrutamiento CERRADA de canal a proveedor de envío. Es la
garantía invariante "WhatsApp nunca por Sent.dm" (`/CLAUDE.md`): no hay
rama, configuración ni fallback que pueda llevar `whatsapp` a otro lado
que no sea Meta. SMS y RCS van siempre a Sent.dm (fase 9), con el token
de plataforma -- nunca a Meta.

No agregues una entrada a `_ENRUTAMIENTO` ni un valor al enum
`ProveedorMensajeria` sin revisar primero esta garantía: cualquier cambio
aquí se revisa explícito contra ella en el PR."""

import enum

from app.app_platform.enums.costo_canal_enums import CanalMensajeria


class ProveedorMensajeria(enum.StrEnum):
    meta = "meta"
    sent = "sent"


class CanalSinProveedorError(ValueError):
    """El canal no tiene proveedor de envío configurado todavía."""


_ENRUTAMIENTO: dict[CanalMensajeria, ProveedorMensajeria | None] = {
    CanalMensajeria.whatsapp: ProveedorMensajeria.meta,
    CanalMensajeria.sms: ProveedorMensajeria.sent,
    CanalMensajeria.rcs: ProveedorMensajeria.sent,
}


def proveedor_de(canal: CanalMensajeria) -> ProveedorMensajeria:
    proveedor = _ENRUTAMIENTO.get(canal)
    if proveedor is None:
        raise CanalSinProveedorError(
            f"El canal {canal.value} no tiene proveedor de envío configurado todavía."
        )
    return proveedor
