"""Punto de entrada, orquestación y manejadores de error de la API REST v1 de MDG Cibersegura."""

from flask import Blueprint, jsonify

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1_bp.errorhandler(400)
def peticion_invalida(e):
    return (
        jsonify(
            {
                "exito": False,
                "error": "Petición no válida o parámetros ausentes.",
                "codigo": "bad_request",
                "detalle": getattr(e, "description", str(e)),
            }
        ),
        400,
    )


@api_v1_bp.errorhandler(401)
def no_autorizado(e):
    return (
        jsonify(
            {
                "exito": False,
                "error": "Autenticación requerida para acceder al recurso.",
                "codigo": "no_autenticado",
                "detalle": getattr(e, "description", str(e)),
            }
        ),
        401,
    )


@api_v1_bp.errorhandler(403)
def acceso_prohibido(e):
    return (
        jsonify(
            {
                "exito": False,
                "error": "Acceso denegado: permisos insuficientes.",
                "codigo": "acceso_denegado",
                "detalle": getattr(e, "description", str(e)),
            }
        ),
        403,
    )


@api_v1_bp.errorhandler(404)
def recurso_no_encontrado(e):
    return (
        jsonify(
            {
                "exito": False,
                "error": "El recurso solicitado no fue encontrado.",
                "codigo": "no_encontrado",
                "detalle": getattr(e, "description", str(e)),
            }
        ),
        404,
    )


@api_v1_bp.errorhandler(405)
def metodo_no_permitido(e):
    return (
        jsonify(
            {
                "exito": False,
                "error": "Método HTTP no permitido para este endpoint.",
                "codigo": "metodo_no_permitido",
            }
        ),
        405,
    )


@api_v1_bp.errorhandler(500)
def error_servidor(e):
    return (
        jsonify(
            {
                "exito": False,
                "error": "Error interno del servidor.",
                "codigo": "error_interno",
            }
        ),
        500,
    )


@api_v1_bp.get("/")
def api_index():
    """Catálogo y documentación interactiva JSON de endpoints expuestos en la API REST v1."""
    return (
        jsonify(
            {
                "nombre": "MDG Cibersegura API REST v1",
                "institucion": "Municipalidad Distrital de Guadalupe",
                "area": "Subgerencia de Informática y TI",
                "version": "1.0.0",
                "estado": "operativo",
                "endpoints": {
                    "salud": "GET /api/v1/salud",
                    "autenticacion": {
                        "login": "POST /api/v1/auth/login",
                        "registro": "POST /api/v1/auth/registro",
                        "logout": "POST /api/v1/auth/logout",
                        "yo": "GET /api/v1/auth/yo",
                    },
                    "aprendizaje": {
                        "temas": "GET /api/v1/temas",
                        "tema_detalle": "GET /api/v1/temas/<id_tema>",
                        "contenido": "GET /api/v1/temas/<id_tema>/contenidos/<id_contenido>",
                        "marcar_completado": "POST /api/v1/temas/<id_tema>/contenidos/<id_contenido>/completar",
                    },
                    "actividades": {
                        "detalle": "GET /api/v1/temas/<id_tema>/actividades/<id_actividad>",
                        "resolver": "POST /api/v1/temas/<id_tema>/actividades/<id_actividad>/resolver",
                    },
                    "evaluaciones": {
                        "cuestionario": "GET /api/v1/temas/<id_tema>/evaluacion",
                        "enviar": "POST /api/v1/temas/<id_tema>/evaluacion/enviar",
                        "resultado": "GET /api/v1/temas/<id_tema>/evaluacion/resultado/<id_intento>",
                    },
                    "progreso": {
                        "mi_progreso": "GET /api/v1/progreso/mi-progreso",
                    },
                    "administracion": {
                        "metricas": "GET /api/v1/admin/metricas",
                        "usuarios": "GET /api/v1/admin/usuarios",
                        "usuario_estado": "PATCH /api/v1/admin/usuarios/<id_usuario>/estado",
                        "contenidos": "GET /api/v1/admin/contenidos",
                        "tema_estado": "PATCH /api/v1/admin/temas/<id_tema>/estado",
                        "contenido_estado": "PATCH /api/v1/admin/contenidos/<id_contenido>/estado",
                        "actividades": "GET /api/v1/admin/actividades",
                        "actividad_estado": "PATCH /api/v1/admin/actividades/<id_actividad>/estado",
                        "evaluaciones": "GET /api/v1/admin/evaluaciones",
                        "evaluacion_estado": "PATCH /api/v1/admin/evaluaciones/<id_evaluacion>/estado",
                    },
                },
            }
        ),
        200,
    )


@api_v1_bp.get("/salud")
def api_salud():
    """Endpoint de verificación de estado y liveness del backend."""
    from app.models.base import utc_now

    return (
        jsonify(
            {
                "estado": "saludable",
                "servicio": "MDG Cibersegura API REST v1",
                "timestamp_utc": utc_now().isoformat(),
            }
        ),
        200,
    )


# Registro de rutas hijas de la API
from app.routes.api.v1 import (  # noqa: E402, F401
    actividades,
    admin,
    auth,
    evaluaciones,
    progreso,
    temas,
)
