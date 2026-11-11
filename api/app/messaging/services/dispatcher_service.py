"""Tabla de enrutamiento CERRADA de canal a proveedor de envío. Es la
garantía invariante "WhatsApp nunca por Sent.dm" (`/CLAUDE.md`): no hay
rama, configuración ni fallback que pueda llevar `whatsapp` a otro lado
que no sea Meta. SMS y RCS (Sent.dm, fase 9) todavía no tienen proveedor
-- se rechazan explícito, nunca se enrutan a ningún sitio por defecto.

No agregues una entrada a `_ENRUTAMIENTO` ni un valor al enum
`ProveedorMensajeria` sin revisar primero esta garantía: cualquier cambio
aquí se revisa explícito contra ella en el PR."""

import enum

from app.app_platform.enums.costo_canal_enums import CanalMensajeria


class ProveedorMensajeria(enum.StrEnum):
    meta = "meta"


class CanalSinProveedorError(ValueError):
    """El canal no tiene proveedor de envío configurado todavía."""


_ENRUTAMIENTO: dict[CanalMensajeria, ProveedorMensajeria | None] = {
    CanalMensajeria.whatsapp: ProveedorMensajeria.meta,
    CanalMensajeria.sms: None,
    CanalMensajeria.rcs: None,
}


def proveedor_de(canal: CanalMensajeria) -> ProveedorMensajeria:
    proveedor = _ENRUTAMIENTO.get(canal)
    if proveedor is None:
        raise CanalSinProveedorError(
            f"El canal {canal.value} no tiene proveedor de envío configurado todavía."
        )
    return proveedor
