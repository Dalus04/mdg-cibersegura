"""Servicio de autenticación, registro y control de cuentas de usuario en MDG Cibersegura."""

from sqlalchemy import select

from app.extensions import db
from app.models.entities import Rol, Usuario

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos."
MENSAJE_CUENTA_INACTIVA = "Tu cuenta no está activa. Contacta a la administración."
MENSAJE_CORREO_REGISTRADO = "Ya existe una cuenta con este correo electrónico."


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
