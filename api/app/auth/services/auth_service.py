"""Registro, login, renovación y cierre de sesión."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.enums.auth_enums import EstadoTenant, RolUsuario
from app.auth.exceptions import CredencialesInvalidasError, LimiteDeIntentosError
from app.auth.models.tenant_model import Tenant
from app.auth.models.usuario_model import Usuario
from app.auth.repositories.tenant_repository import TenantRepository
from app.auth.repositories.usuario_repository import UsuarioRepository
from app.auth.schemas.auth_schemas import LoginRequest, RegistroRequest
from app.auth.schemas.sesion_schema import SesionUsuario
from app.auth.services.sesion_service import SesionService
from app.core.security.password_hasher import PasswordHasherService
from app.core.security.token_service import TokenService
from app.core.valkey.client import increment_with_ttl, valkey_client

TRIAL_DIAS = 14
MAXIMO_INTENTOS_LOGIN = 10
BLOQUEO_LOGIN_SEGUNDOS = 15 * 60
_CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos."


class AuthResultado:
    def __init__(self, usuario: Usuario, access_token: str, refresh_token: str):
        self.usuario = usuario
        self.access_token = access_token
        self.refresh_token = refresh_token


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        usuario_repository: UsuarioRepository,
        tenant_repository: TenantRepository,
    ):
        self.session = session
        self.usuario_repository = usuario_repository
        self.tenant_repository = tenant_repository
        self.password_hasher = PasswordHasherService()
        self.token_service = TokenService()
        self.sesion_service = SesionService()
        self._hash_dummy: str | None = None

    def _clave_fallos_login(self, email: str) -> str:
        return f"login-fail:{email}"

    def _hash_para_timing(self) -> str:
        if self._hash_dummy is None:
            self._hash_dummy = self.password_hasher.hash_password(
                "contraseña-de-referencia-para-timing"
            )
        return self._hash_dummy

    async def registrar(self, datos: RegistroRequest) -> AuthResultado:
        email = datos.email.strip().lower()
        if await self.usuario_repository.obtener_por_email_global(email):
            raise ValueError("El correo ya está registrado.")

        ahora = datetime.now(UTC)
        tenant = await self.tenant_repository.add(
            Tenant(
                nombre=datos.nombre_organizacion,
                estado=EstadoTenant.trial,
                trial_fin=ahora + timedelta(days=TRIAL_DIAS),
            )
        )
        usuario = await self.usuario_repository.add(
            Usuario(
                tenant_id=tenant.id,
                email=email,
                password_hash=self.password_hasher.hash_password(datos.password),
                rol=RolUsuario.administrador,
                mfa_habilitado=True,
                activo=True,
            )
        )
        await self.session.commit()
        return await self._emitir_tokens(usuario, login_nuevo=True)

    async def login(self, datos: LoginRequest) -> AuthResultado:
        email = datos.email.strip().lower()
        clave_fallos = self._clave_fallos_login(email)

        fallos = await valkey_client.get(clave_fallos)
        if fallos is not None and int(fallos) >= MAXIMO_INTENTOS_LOGIN:
            raise LimiteDeIntentosError(
                "Demasiados intentos fallidos. Espera unos minutos."
            )

        usuario = await self.usuario_repository.obtener_por_email_global(email)
        hash_guardado = usuario.password_hash if usuario else None
        if not hash_guardado:
            self.password_hasher.verify_and_maybe_rehash(
                self._hash_para_timing(), datos.password
            )
            await increment_with_ttl(clave_fallos, BLOQUEO_LOGIN_SEGUNDOS)
            raise CredencialesInvalidasError(_CREDENCIALES_INVALIDAS)

        valido, nuevo_hash = self.password_hasher.verify_and_maybe_rehash(
            hash_guardado, datos.password
        )
        if not valido:
            await increment_with_ttl(clave_fallos, BLOQUEO_LOGIN_SEGUNDOS)
            raise CredencialesInvalidasError(_CREDENCIALES_INVALIDAS)

        if not usuario.activo:
            raise CredencialesInvalidasError(_CREDENCIALES_INVALIDAS)

        await valkey_client.delete(clave_fallos)
        if nuevo_hash:
            usuario.password_hash = nuevo_hash
            await self.usuario_repository.update(usuario)
            await self.session.commit()

        return await self._emitir_tokens(usuario, login_nuevo=True)

    async def refrescar(self, refresh_token: str) -> AuthResultado:
        payload = self.token_service.verificar_refresh_token_jwt(refresh_token)
        usuario_id = int(payload["sub"])
        jti = payload["jti"]

        if not await self.token_service.refresh_token_vigente(usuario_id, jti):
            raise CredencialesInvalidasError("Sesión inválida o ya cerrada.")

        usuario = await self.usuario_repository.obtener_por_id_global(usuario_id)
        if usuario is None or not usuario.activo:
            raise CredencialesInvalidasError("Usuario no encontrado.")

        await self.token_service.revocar_refresh_token(usuario_id)
        return await self._emitir_tokens(usuario, login_nuevo=False)

    async def cerrar_sesion(self, usuario_id: int) -> None:
        await self.token_service.revocar_refresh_token(usuario_id)
        await self.sesion_service.eliminar(usuario_id)

    async def obtener_usuario(self, usuario_id: int) -> Usuario | None:
        return await self.usuario_repository.get_by_id(usuario_id)

    async def _emitir_tokens(
        self, usuario: Usuario, *, login_nuevo: bool
    ) -> AuthResultado:
        if login_nuevo:
            # Cada login nuevo vuelve a exigir el segundo factor, aunque quede
            # un flag de una sesión anterior sin expirar (refrescar() no pasa
            # por aquí con login_nuevo=True: renovar el access token cada hora
            # no debe re-pedir MFA).
            await self.sesion_service.invalidar_mfa(usuario.id)
        sesion: SesionUsuario = await self.sesion_service.construir_y_guardar(usuario)
        access_token = self.token_service.generar_access_token(
            sesion.usuario_id, sesion.email
        )
        refresh_token = await self.token_service.generar_refresh_token(usuario.id)
        return AuthResultado(usuario, access_token, refresh_token)
