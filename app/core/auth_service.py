"""Servicio de autenticación, registro y control de cuentas de usuario en MDG Cibersegura."""

from sqlalchemy import select

from app.extensions import db
from app.models.entities import Rol, Usuario

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos."
MENSAJE_CUENTA_INACTIVA = "Tu cuenta no está activa. Contacta a la administración."
MENSAJE_CORREO_REGISTRADO = "Ya existe una cuenta con este correo electrónico."
MENSAJE_ENLACE_INVALIDO = "El enlace de recuperación no es válido o está incompleto."
MENSAJE_ENLACE_EXPIRADO = "El enlace de recuperación ha expirado. Solicita uno nuevo."
SALT_RECUPERACION = "recuperar-password"


class AuthService:
    """Orquesta las operaciones de identidad, registro ciudadano y validación de credenciales."""

    @classmethod
    def registrar_ciudadano(
        cls, nombres: str, apellidos: str, correo: str, password: str
    ) -> tuple[bool, Usuario | None, str | None]:
        """Crea una nueva cuenta ciudadana con rol 'ciudadano' y contraseña cifrada con hash seguro."""
        correo_limpio = Usuario.normalizar_correo(correo)
        existente = Usuario.buscar_por_correo(correo_limpio)
        if existente is not None:
            return False, None, MENSAJE_CORREO_REGISTRADO

        rol_ciudadano = db.session.scalar(select(Rol).where(Rol.nombre == "ciudadano"))
        if rol_ciudadano is None:
            return False, None, "No se encontró el rol institucional de ciudadano configurado en el sistema."

        usuario = Usuario(
            id_rol=rol_ciudadano.id_rol,
            nombres=nombres.strip(),
            apellidos=apellidos.strip(),
            correo=correo_limpio,
            estado="activo",
        )
        usuario.set_password(password)

        db.session.add(usuario)
        db.session.commit()

        return True, usuario, None

    @classmethod
    def autenticar_usuario(
        cls, correo: str, password: str
    ) -> tuple[bool, Usuario | None, str | None]:
        """Verifica las credenciales y el estado activo del usuario."""
        usuario = Usuario.autenticar(correo, password)
        if usuario is None:
            return False, None, MENSAJE_CREDENCIALES

        if not usuario.is_active:
            return False, None, MENSAJE_CUENTA_INACTIVA

        return True, usuario, None

    @classmethod
    def generar_token_recuperacion(cls, correo: str) -> tuple[bool, str | None, str | None]:
        """Genera un token firmado criptográficamente de tiempo limitado para recuperación de contraseña."""
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer

        correo_limpio = Usuario.normalizar_correo(correo)
        usuario = Usuario.buscar_por_correo(correo_limpio)
        if usuario is None or not usuario.is_active:
            # Prevención de enumeración de usuarios
            return False, None, None

        secret = current_app.config["SECRET_KEY"]
        serializer = URLSafeTimedSerializer(secret)
        token = serializer.dumps({"id_usuario": usuario.id_usuario}, salt=SALT_RECUPERACION)
        return True, token, None

    @classmethod
    def validar_token_recuperacion(
        cls, token: str, max_age: int = 3600
    ) -> tuple[bool, Usuario | None, str | None]:
        """Valida la autenticidad y caducidad del token de recuperación y retorna el usuario."""
        from flask import current_app
        from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

        secret = current_app.config["SECRET_KEY"]
        serializer = URLSafeTimedSerializer(secret)
        try:
            datos = serializer.loads(token, salt=SALT_RECUPERACION, max_age=max_age)
        except SignatureExpired:
            return False, None, MENSAJE_ENLACE_EXPIRADO
        except BadSignature:
            return False, None, MENSAJE_ENLACE_INVALIDO

        id_usuario = datos.get("id_usuario")
        if not id_usuario:
            return False, None, MENSAJE_ENLACE_INVALIDO

        usuario = db.session.get(Usuario, id_usuario)
        if usuario is None or not usuario.is_active:
            return False, None, MENSAJE_ENLACE_INVALIDO

        return True, usuario, None

    @classmethod
    def restablecer_password(
        cls, usuario: Usuario, nuevo_password: str
    ) -> tuple[bool, str | None]:
        """Actualiza la contraseña del usuario con un hash seguro y persiste los cambios."""
        usuario.set_password(nuevo_password)
        db.session.commit()
        return True, None
