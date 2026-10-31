"""Decoradores de control de acceso y autorización por roles para MDG Cibersegura."""

from functools import wraps

from flask import abort, flash, jsonify, redirect, request, url_for
from flask_login import current_user


def admin_required(fn):
    """Verifica que el usuario esté autenticado y posea el rol de administrador institucional.

    Distingue automáticamente entre solicitudes de la API REST (respondiendo con JSON y códigos
    401/403) y solicitudes Web SSR (redirigiendo a login o abortando con código 403).
    """

    @wraps(fn)
    def decorated_view(*args, **kwargs):
        es_api = request.path.startswith("/api/") or request.is_json

        if not current_user.is_authenticated:
            if es_api:
                return (
                    jsonify(
                        {
                            "exito": False,
                            "error": "Autenticación requerida para acceder a este recurso.",
                            "codigo": "no_autenticado",
                        }
                    ),
                    401,
                )
            flash("Debes iniciar sesión con una cuenta administrativa para continuar.", "error")
            return redirect(url_for("auth.login", next=request.full_path))

        if not getattr(current_user, "es_administrador", False):
            if es_api:
                return (
                    jsonify(
                        {
                            "exito": False,
                            "error": "Acceso denegado: se requieren privilegios de administrador.",
                            "codigo": "acceso_denegado",
                        }
                    ),
                    403,
                )
            flash("No tienes permisos suficientes para acceder al módulo de administración.", "error")
            abort(403)

        return fn(*args, **kwargs)

    return decorated_view


def api_login_required(fn):
    """Valida la autenticación para endpoints JSON, retornando 401 JSON en lugar de redirección HTML."""

    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return (
                jsonify(
                    {
                        "exito": False,
                        "error": "Autenticación requerida para acceder a este recurso.",
                        "codigo": "no_autenticado",
                    }
                ),
                401,
            )
        return fn(*args, **kwargs)

    return decorated_view
