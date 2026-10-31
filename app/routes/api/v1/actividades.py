"""Endpoints de actividades prácticas y simulaciones interactivas en la API REST v1."""

from flask import jsonify, request
from flask_login import current_user
from sqlalchemy import select

from app.core import ActividadService, api_login_required
from app.extensions import db
from app.models.entities import Actividad
from app.routes.api.v1 import api_v1_bp


@api_v1_bp.get("/temas/<int:id_tema>/actividades/<int:id_actividad>")
def api_ver_actividad(id_tema: int, id_actividad: int):
    """Retorna la actividad o simulación interactiva con sus instrucciones sanitizadas."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    actividad_data = ActividadService.obtener_actividad_para_resolver(
        id_tema=id_tema,
        id_actividad=id_actividad,
        id_usuario=id_usuario,
    )

    if actividad_data is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "La actividad solicitada no existe o no se encuentra publicada.",
                    "codigo": "actividad_no_encontrada",
                }
            ),
            404,
        )

    config = actividad_data["configuracion"]
    # Sanitizar opciones para no revelar 'es_correcta' ni 'explicacion' antes de resolver
    opciones_sanitizadas = []
    for opt in config.get("opciones", []):
        opciones_sanitizadas.append(
            {
                "id": opt.get("id"),
                "texto": opt.get("texto"),
            }
        )

    ultimo = actividad_data["ultimo_intento"]

    return (
        jsonify(
            {
                "exito": True,
                "tema": {
                    "id_tema": actividad_data["tema"].id_tema,
                    "titulo": actividad_data["tema"].titulo,
                },
                "actividad": {
                    "id_actividad": actividad_data["actividad"].id_actividad,
                    "titulo": actividad_data["actividad"].titulo,
                    "tipo": actividad_data["actividad"].tipo,
                    "introduccion": config.get("introduccion"),
                    "caso_contexto": config.get("caso_contexto"),
                    "correo_simulado": config.get("correo_simulado"),
                    "opciones": opciones_sanitizadas,
                    "ultimo_intento": {
                        "resultado": ultimo.resultado,
                        "fecha_intento": ultimo.fecha_intento.isoformat() if ultimo.fecha_intento else None,
                    }
                    if ultimo
                    else None,
                },
            }
        ),
        200,
    )


@api_v1_bp.get("/actividades/<int:id_actividad>")
def api_ver_actividad_directa(id_actividad: int):
    """Ruta directa para consultar una actividad por su ID único."""
    actividad = db.session.scalar(
        select(Actividad).where(Actividad.id_actividad == id_actividad, Actividad.estado == "publicado")
    )
    if actividad is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Actividad no encontrada.",
                    "codigo": "actividad_no_encontrada",
                }
            ),
            404,
        )
    return api_ver_actividad(id_tema=actividad.id_tema, id_actividad=id_actividad)


@api_v1_bp.post("/temas/<int:id_tema>/actividades/<int:id_actividad>/resolver")
@api_login_required
def api_resolver_actividad(id_tema: int, id_actividad: int):
    """Evalúa la alternativa seleccionada en la simulación o taller y persiste el intento."""
    data = request.get_json(silent=True) or {}
    opcion_id = data.get("opcion_id")

    if not opcion_id:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe especificar el parámetro 'opcion_id'.",
                    "codigo": "opcion_requerida",
                }
            ),
            400,
        )

    exito, resultado_data, error_msg = ActividadService.procesar_resolucion_actividad(
        id_tema=id_tema,
        id_actividad=id_actividad,
        id_usuario=current_user.id_usuario,
        opcion_id=str(opcion_id),
    )

    if not exito or resultado_data is None:
        codigo_http = 404 if "no existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al procesar la resolución de la actividad.",
                    "codigo": "error_resolucion",
                }
            ),
            codigo_http,
        )

    intento = resultado_data["intento"]
    opcion = resultado_data["opcion_elegida"]

    return (
        jsonify(
            {
                "exito": True,
                "es_correcta": resultado_data["es_correcta"],
                "resultado_clave": intento.resultado,
                "retroalimentacion": opcion.get("retroalimentacion"),
                "explicacion": opcion.get("explicacion"),
                "intento": {
                    "id_intento_actividad": intento.id_intento_actividad,
                    "fecha_intento": intento.fecha_intento.isoformat() if intento.fecha_intento else None,
                },
            }
        ),
        200,
    )


@api_v1_bp.post("/actividades/<int:id_actividad>/resolver")
@api_login_required
def api_resolver_actividad_directa(id_actividad: int):
    """Ruta directa para resolver una actividad sin requerir el id_tema en la URL."""
    actividad = db.session.scalar(
        select(Actividad).where(Actividad.id_actividad == id_actividad, Actividad.estado == "publicado")
    )
    if actividad is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Actividad no encontrada.",
                    "codigo": "actividad_no_encontrada",
                }
            ),
            404,
        )
    return api_resolver_actividad(id_tema=actividad.id_tema, id_actividad=id_actividad)
