"""Registro, login, renovación y cierre de sesión."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.app_platform.exceptions import (
    LimiteDePlanError,
    ParametroComercialFaltanteError,
)
from app.app_platform.services.parametro_comercial_service import (
    ParametroComercialService,
)
from app.app_platform.services.plan_service import PlanService
from app.auth.enums.auth_enums import EstadoTenant, RolUsuario
from app.auth.exceptions import (
    CredencialesInvalidasError,
    LimiteDeIntentosError,
    PermisoInsuficienteError,
)
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

# Plan asignado por defecto a todo tenant nuevo hasta que exista billing
# (Prompt 12) y el tenant elija/pague uno: el más chico, no "sin plan" --
# así el límite de usuarios/números ya aplica desde el registro.
PLAN_POR_DEFECTO = "Esencial"
CLAVE_TRIAL_DIAS = "trial_dias"
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
        plan_service: PlanService,
        parametro_comercial_service: ParametroComercialService,
    ):
        self.session = session
        self.usuario_repository = usuario_repository
        self.tenant_repository = tenant_repository
        self.plan_service = plan_service
        self.parametro_comercial_service = parametro_comercial_service
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

        plan = await self.plan_service.obtener_por_nombre(PLAN_POR_DEFECTO)
        if plan is None:
            raise ParametroComercialFaltanteError(
                f"No existe el plan por defecto '{PLAN_POR_DEFECTO}'."
            )
        trial_dias = await self.parametro_comercial_service.valor_vigente(
            CLAVE_TRIAL_DIAS, date.today()
        )
        if trial_dias is None:
            raise ParametroComercialFaltanteError(
                f"No hay valor vigente para el parámetro '{CLAVE_TRIAL_DIAS}'."
            )

        ahora = datetime.now(UTC)
        tenant = await self.tenant_repository.add(
            Tenant(
                nombre=datos.nombre_organizacion,
                estado=EstadoTenant.trial,
                trial_fin=ahora + timedelta(days=int(trial_dias)),
                plan_id=plan.id,
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

    async def invitar_usuario(
        self, sesion: SesionUsuario, email: str, password: str
    ) -> Usuario:
        """Alta de un usuario adicional en la organización de `sesion`.
        Exige rol administrador y respeta `max_usuarios` del plan vigente
        del tenant (`/CLAUDE.md`, «Aplicación de los límites...»): no se
        crea el usuario si el límite ya se alcanzó."""

        if sesion.rol != RolUsuario.administrador:
            raise PermisoInsuficienteError(
                "Solo un administrador de la organización puede invitar usuarios."
            )

        tenant = await self.tenant_repository.get_by_id(sesion.tenant_id)
        if tenant is None or tenant.plan_id is None:
            raise LimiteDePlanError(
                "Esta organización no tiene un plan asignado todavía."
            )
        plan = await self.plan_service.obtener(tenant.plan_id)
        if plan is None:
            raise LimiteDePlanError(
                "El plan asignado a esta organización ya no existe."
            )

        usuarios_actuales = await self.usuario_repository.get_all()
        await self.plan_service.verificar_limite_usuarios(plan, len(usuarios_actuales))

        email_normalizado = email.strip().lower()
        if await self.usuario_repository.obtener_por_email_global(email_normalizado):
            raise ValueError("El correo ya está registrado.")

        nuevo = await self.usuario_repository.add(
            Usuario(
                tenant_id=sesion.tenant_id,
                email=email_normalizado,
                password_hash=self.password_hasher.hash_password(password),
                rol=RolUsuario.miembro,
                mfa_habilitado=True,
                activo=True,
            )
        )
        await self.session.commit()
        return nuevo

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
