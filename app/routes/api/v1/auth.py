"""Endpoints de autenticación, registro y control de sesión en la API REST v1."""

from flask import jsonify, request
from flask_login import current_user, login_user, logout_user

from app.core.auth_service import AuthService
from app.routes.api.v1 import api_v1_bp


@api_v1_bp.post("/auth/login")
def api_login():
    """Autentica a un usuario y establece la sesión de cliente."""
    data = request.get_json(silent=True) or {}
    correo = data.get("correo")
    password = data.get("password") or data.get("contrasena")

    if not correo or not password:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe proporcionar 'correo' y 'password'.",
                    "codigo": "campos_requeridos",
                }
            ),
            400,
        )

    exito, usuario, error_msg = AuthService.autenticar_usuario(correo=str(correo), password=str(password))
    if not exito or usuario is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Credenciales incorrectas.",
                    "codigo": "credenciales_invalidas",
                }
            ),
            401,
        )

    login_user(usuario)
    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Bienvenido(a), {usuario.nombres}.",
                "usuario": {
                    "id_usuario": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "nombre_completo": usuario.nombre_completo,
                    "correo": usuario.correo,
                    "rol": usuario.rol.nombre if usuario.rol else "ciudadano",
                    "es_administrador": usuario.es_administrador,
                },
            }
        ),
        200,
    )


@api_v1_bp.post("/auth/registro")
def api_registro():
    """Registra una nueva cuenta de ciudadano con validaciones de servidor."""
    data = request.get_json(silent=True) or {}
    nombres = str(data.get("nombres") or "").strip()
    apellidos = str(data.get("apellidos") or "").strip()
    correo = str(data.get("correo") or "").strip()
    password = str(data.get("password") or data.get("contrasena") or "")

    if not nombres or not apellidos or not correo or not password:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Todos los campos ('nombres', 'apellidos', 'correo', 'password') son obligatorios.",
                    "codigo": "campos_requeridos",
                }
            ),
            400,
        )

    if len(password) < 8:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "La contraseña debe tener al menos 8 caracteres.",
                    "codigo": "password_corta",
                }
            ),
            400,
        )

    exito, usuario, error_msg = AuthService.registrar_ciudadano(
        nombres=nombres,
        apellidos=apellidos,
        correo=correo,
        password=password,
    )

    if not exito or usuario is None:
        status_code = 409 if "existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al crear la cuenta.",
                    "codigo": "registro_fallido",
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": "Cuenta de ciudadano creada correctamente.",
                "usuario": {
                    "id_usuario": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "nombre_completo": usuario.nombre_completo,
                    "correo": usuario.correo,
                    "rol": usuario.rol.nombre if usuario.rol else "ciudadano",
                    "es_administrador": usuario.es_administrador,
                },
            }
        ),
        201,
    )


@api_v1_bp.post("/auth/logout")
def api_logout():
    """Finaliza la sesión del usuario actual."""
    if current_user.is_authenticated:
        logout_user()
    return (
        jsonify(
            {
                "exito": True,
                "mensaje": "Sesión finalizada exitosamente.",
            }
        ),
        200,
    )


@api_v1_bp.get("/auth/yo")
def api_yo():
    """Retorna los datos de perfil del usuario con sesión activa."""
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "No hay una sesión activa.",
                    "codigo": "no_autenticado",
                }
            ),
            401,
        )

    return (
        jsonify(
            {
                "exito": True,
                "usuario": {
                    "id_usuario": current_user.id_usuario,
                    "nombres": current_user.nombres,
                    "apellidos": current_user.apellidos,
                    "nombre_completo": current_user.nombre_completo,
                    "correo": current_user.correo,
                    "rol": current_user.rol.nombre if current_user.rol else "sin_rol",
                    "es_administrador": current_user.es_administrador,
                    "fecha_registro": current_user.fecha_registro.isoformat()
                    if current_user.fecha_registro
                    else None,
                },
            }
        ),
        200,
    )
