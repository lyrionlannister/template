"""Cableado de inyección de auth: token de cookie, sesión, servicios.

`get_sesion_actual` es la dependencia central que entrega la sesión vigente
a los controladores: carga la sesión desde Valkey y, mientras dura la
petición, fija el contexto de tenant
(`set_current_tenant`) para que `TenantScopedRepository` filtre solo. Un
access token válido sin sesión en Valkey no sirve, aunque no haya expirado.
"""

from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.dependencies import (
    get_parametro_comercial_service,
    get_plan_service,
)
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.auth.repositories.codigo_otp_repository import CodigoOtpRepository
from app.auth.repositories.tenant_repository import TenantRepository
from app.auth.repositories.usuario_repository import UsuarioRepository
from app.auth.schemas.sesion_schema import SesionUsuario
from app.auth.services.auth_service import AuthService
from app.auth.services.otp_service import OtpService
from app.auth.services.sesion_service import SesionService
from app.core.database.session import get_db_session
from app.core.database.tenant_context import set_current_tenant
from app.core.security.cookies import ACCESS_TOKEN_COOKIE
from app.core.security.token_service import TokenInvalidoError, TokenService

_token_service = TokenService()
_sesion_service = SesionService()


def _obtener_token_payload(request: Request) -> dict[str, Any]:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada. Inicia sesión nuevamente.",
        )
    try:
        return _token_service.verificar_access_token(token)
    except TokenInvalidoError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)
        ) from error


def _usuario_id_del_payload(payload: dict[str, Any]) -> int:
    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido."
        ) from error


TokenPayload = Annotated[dict[str, Any], Depends(_obtener_token_payload)]


async def get_sesion_pendiente_mfa(
    payload: TokenPayload,
) -> AsyncGenerator[SesionUsuario]:
    """Sesión vigente sin exigir el segundo factor: solo la usan los
    endpoints de OTP, que deben quedar accesibles mientras el MFA sigue
    pendiente."""

    usuario_id = _usuario_id_del_payload(payload)
    sesion = await _sesion_service.cargar(usuario_id)
    if sesion is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada. Inicia sesión nuevamente.",
        )
    with set_current_tenant(sesion.tenant_id):
        yield sesion


async def get_sesion_actual(
    sesion: Annotated[SesionUsuario, Depends(get_sesion_pendiente_mfa)],
) -> SesionUsuario:
    if sesion.mfa_habilitado and not await _sesion_service.mfa_fue_verificado(
        sesion.usuario_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verificación de dos pasos pendiente.",
        )
    return sesion


SesionPendienteMfa = Annotated[SesionUsuario, Depends(get_sesion_pendiente_mfa)]
SesionActual = Annotated[SesionUsuario, Depends(get_sesion_actual)]


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    plan_service: Annotated[PlanService, Depends(get_plan_service)],
    parametro_comercial_service: Annotated[
        ParametroComercialService, Depends(get_parametro_comercial_service)
    ],
) -> AuthService:
    return AuthService(
        session=session,
        usuario_repository=UsuarioRepository(session),
        tenant_repository=TenantRepository(session),
        plan_service=plan_service,
        parametro_comercial_service=parametro_comercial_service,
    )


def get_otp_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OtpService:
    return OtpService(CodigoOtpRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
OtpServiceDep = Annotated[OtpService, Depends(get_otp_service)]
