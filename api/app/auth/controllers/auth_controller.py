"""Endpoints de autenticación: registro, login, OTP/MFA, refresh, logout."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.dependencies import (
    AuthServiceDep,
    OtpServiceDep,
    SesionActual,
    SesionPendienteMfa,
)
from app.auth.exceptions import (
    CodigoOtpExpiradoError,
    CodigoOtpNoEncontradoError,
    CodigoOtpYaUsadoError,
    CredencialesInvalidasError,
    LimiteDeIntentosError,
)
from app.auth.schemas.auth_schemas import (
    LoginRequest,
    OtpEnviarRequest,
    OtpVerificarRequest,
    RegistroRequest,
    UsuarioRespuesta,
)
from app.auth.services.auth_service import AuthResultado
from app.auth.services.sesion_service import SesionService
from app.core.security.cookies import (
    REFRESH_TOKEN_COOKIE,
    clear_auth_cookies,
    set_auth_cookies,
)
from app.core.security.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

_limite_auth = Depends(rate_limit("auth", maximo_intentos=20, ventana_segundos=60))


def _respuesta_de(resultado: AuthResultado, response: Response) -> UsuarioRespuesta:
    set_auth_cookies(response, resultado.access_token, resultado.refresh_token)
    usuario = resultado.usuario
    return UsuarioRespuesta(
        public_id=usuario.public_id,
        email=usuario.email,
        rol=usuario.rol,
        mfa_habilitado=usuario.mfa_habilitado,
    )


@router.post(
    "/registro",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_limite_auth],
)
async def registrar(
    body: RegistroRequest, response: Response, service: AuthServiceDep
) -> UsuarioRespuesta:
    try:
        resultado = await service.registrar(body)
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return _respuesta_de(resultado, response)


@router.post("/login", response_model=UsuarioRespuesta, dependencies=[_limite_auth])
async def login(
    body: LoginRequest, response: Response, service: AuthServiceDep
) -> UsuarioRespuesta:
    try:
        resultado = await service.login(body)
    except CredencialesInvalidasError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error
    except LimiteDeIntentosError as error:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(error)) from error
    return _respuesta_de(resultado, response)


@router.post(
    "/otp/enviar", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_limite_auth]
)
async def enviar_otp(
    body: OtpEnviarRequest, sesion: SesionPendienteMfa, service: OtpServiceDep
) -> None:
    await service.enviar(sesion.tenant_id, sesion.usuario_id, body.canal)


@router.post(
    "/otp/verificar",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_limite_auth],
)
async def verificar_otp(
    body: OtpVerificarRequest, sesion: SesionPendienteMfa, service: OtpServiceDep
) -> None:
    try:
        await service.verificar(sesion.usuario_id, body.codigo, body.canal)
    except CodigoOtpNoEncontradoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Código incorrecto.") from (
            error
        )
    except CodigoOtpExpiradoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except CodigoOtpYaUsadoError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except LimiteDeIntentosError as error:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(error)) from error

    await SesionService().marcar_mfa_verificado(sesion.usuario_id)


@router.post("/refresh", response_model=UsuarioRespuesta)
async def refrescar(
    request: Request, response: Response, service: AuthServiceDep
) -> UsuarioRespuesta:
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not refresh_token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "No se encontró un refresh token."
        )
    try:
        resultado = await service.refrescar(refresh_token)
    except CredencialesInvalidasError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(error)) from error
    return _respuesta_de(resultado, response)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    sesion: SesionPendienteMfa, response: Response, service: AuthServiceDep
) -> dict:
    await service.cerrar_sesion(sesion.usuario_id)
    clear_auth_cookies(response)
    return {"mensaje": "Sesión cerrada."}


@router.get("/yo", response_model=UsuarioRespuesta)
async def quien_soy(sesion: SesionActual, service: AuthServiceDep) -> UsuarioRespuesta:
    usuario = await service.obtener_usuario(sesion.usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")
    return UsuarioRespuesta(
        public_id=usuario.public_id,
        email=usuario.email,
        rol=usuario.rol,
        mfa_habilitado=usuario.mfa_habilitado,
    )
