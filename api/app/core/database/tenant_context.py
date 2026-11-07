"""Contexto de tenant de la petición en curso.

No existen consultas "globales" fuera del administrador del sistema. Por
eso el default aquí es cerrado: si nadie fijó un tenant, pedir
el tenant actual falla en vez de devolver `None` silenciosamente — un `None`
por descuido en una query sin filtrar sería una fuga entre tenants, no un
error visible. El único bypass es `allow_system_scope()`, explícito y para
usar solo desde el dominio `app_platform` (administrador del sistema).
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


class TenantContextError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Scope:
    tenant_id: int | None
    is_system_scope: bool


_current_scope: ContextVar[_Scope | None] = ContextVar("_current_scope", default=None)


@contextmanager
def set_current_tenant(tenant_id: int):
    token = _current_scope.set(_Scope(tenant_id=tenant_id, is_system_scope=False))
    try:
        yield
    finally:
        _current_scope.reset(token)


@contextmanager
def allow_system_scope():
    """Bypass explícito del filtro de tenant, para el administrador del sistema."""

    token = _current_scope.set(_Scope(tenant_id=None, is_system_scope=True))
    try:
        yield
    finally:
        _current_scope.reset(token)


def get_current_tenant_id() -> int:
    """Tenant de la petición en curso. Falla si nadie lo fijó."""

    scope = _current_scope.get()
    if scope is None:
        raise TenantContextError(
            "No hay tenant en contexto. Usa set_current_tenant() o, si de verdad "
            "es una operación de administrador del sistema, allow_system_scope()."
        )
    if scope.is_system_scope:
        raise TenantContextError(
            "El contexto actual es de administrador del sistema (sin tenant): "
            "esta operación requiere un tenant."
        )
    return scope.tenant_id


def is_system_scope() -> bool:
    scope = _current_scope.get()
    return scope is not None and scope.is_system_scope
