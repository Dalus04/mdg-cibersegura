"""Endpoints de cuestionarios formales, calificación y retroalimentación de evaluaciones en la API REST v1."""

from flask import jsonify, request
from flask_login import current_user

from app.core import EvaluacionService, api_login_required
from app.routes.api.v1 import api_v1_bp


@api_v1_bp.get("/temas/<int:id_tema>/evaluacion")
def api_ver_evaluacion(id_tema: int):
    """Retorna las preguntas y alternativas del cuestionario formal de un tema."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    eval_data = EvaluacionService.obtener_evaluacion_tema(id_tema, id_usuario)

    if eval_data is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "No existe una evaluación publicada para este tema.",
                    "codigo": "evaluacion_no_encontrada",
                }
            ),
            404,
        )

    evaluacion = eval_data["evaluacion"]
    preguntas_list = []
    for preg in evaluacion.preguntas:
        # Sanitizar alternativas para no exponer 'es_correcta'
        alts = [
            {
                "id_alternativa": alt.id_alternativa,
                "texto": alt.texto,
            }
            for alt in preg.alternativas
        ]
        preguntas_list.append(
            {
                "id_pregunta": preg.id_pregunta,
                "enunciado": preg.enunciado,
                "puntaje": preg.puntaje,
                "alternativas": alts,
            }
        )

    mejor = eval_data["mejor_intento"]
    ultimo = eval_data["ultimo_intento"]

    return (
        jsonify(
            {
                "exito": True,
                "tema": {
                    "id_tema": eval_data["tema"].id_tema,
                    "titulo": eval_data["tema"].titulo,
                },
                "evaluacion": {
                    "id_evaluacion": evaluacion.id_evaluacion,
                    "titulo": evaluacion.titulo,
                    "puntaje_minimo": evaluacion.puntaje_minimo,
                    "puntaje_maximo": evaluacion.puntaje_maximo,
                    "total_preguntas": len(preguntas_list),
                    "preguntas": preguntas_list,
                    "historial_usuario": {
                        "mejor_intento": {
                            "id_intento": mejor.id_intento_evaluacion,
                            "puntaje_obtenido": mejor.puntaje_obtenido,
                            "aprobado": mejor.aprobado,
                            "fecha_intento": mejor.fecha_intento.isoformat() if mejor.fecha_intento else None,
                        }
                        if mejor
                        else None,
                        "ultimo_intento": {
                            "id_intento": ultimo.id_intento_evaluacion,
                            "puntaje_obtenido": ultimo.puntaje_obtenido,
                            "aprobado": ultimo.aprobado,
                            "fecha_intento": ultimo.fecha_intento.isoformat() if ultimo.fecha_intento else None,
                        }
                        if ultimo
                        else None,
                    }
                    if id_usuario
                    else None,
                },
            }
        ),
        200,
    )


@api_v1_bp.post("/temas/<int:id_tema>/evaluacion/enviar")
@api_login_required
def api_enviar_evaluacion(id_tema: int):
    """Califica las respuestas remitidas por el ciudadano y persiste el intento formal."""
    json_data = request.get_json(silent=True) or {}
    respuestas_input = json_data.get("respuestas")

    # Admite formato dict {"respuestas": {"1": 4, "2": 7}} o {"pregunta_1": 4, "pregunta_2": 7}
    form_data: dict[str, str] = {}
    if isinstance(respuestas_input, dict):
        for k, v in respuestas_input.items():
            key = f"pregunta_{k}" if not str(k).startswith("pregunta_") else str(k)
            form_data[key] = str(v)
    else:
        for k, v in json_data.items():
            if str(k).startswith("pregunta_"):
                form_data[str(k)] = str(v)

    if not form_data:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "No se recibieron respuestas. Envíe un objeto 'respuestas' con el mapa de pregunta a alternativa.",
                    "codigo": "respuestas_vacias",
                }
            ),
            400,
        )

    exito, intento, error_msg = EvaluacionService.calificar_y_registrar_intento(
        id_tema=id_tema,
        id_usuario=current_user.id_usuario,
        form_data=form_data,
    )

    if not exito or intento is None:
        status_code = 404 if "no existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al calificar la evaluación.",
                    "codigo": "error_calificacion",
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": (
                    f"Evaluación completada. Nota obtenida: {intento.puntaje_obtenido:.1f} puntos."
                ),
                "intento": {
                    "id_intento_evaluacion": intento.id_intento_evaluacion,
                    "id_evaluacion": intento.id_evaluacion,
                    "id_tema": id_tema,
                    "puntaje_obtenido": intento.puntaje_obtenido,
                    "puntaje_minimo": intento.evaluacion.puntaje_minimo,
                    "aprobado": intento.aprobado,
                    "fecha_intento": intento.fecha_intento.isoformat() if intento.fecha_intento else None,
                },
            }
        ),
        201,
    )


@api_v1_bp.get("/temas/<int:id_tema>/evaluacion/resultado/<int:id_intento>")
@api_login_required
def api_resultado_evaluacion(id_tema: int, id_intento: int):
    """Muestra el desglose detallado de aciertos y desaciertos de un intento del usuario."""
    resultado_data = EvaluacionService.obtener_resultado_intento(
        id_tema=id_tema,
        id_intento=id_intento,
        id_usuario=current_user.id_usuario,
    )

    if resultado_data is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "El intento de evaluación solicitado no existe o no pertenece a tu cuenta.",
                    "codigo": "intento_no_encontrado",
                }
            ),
            404,
        )

    intento = resultado_data["intento"]
    evaluacion = resultado_data["evaluacion"]
    respuestas_map = resultado_data["respuestas_por_pregunta"]

    desglose_preguntas = []
    for preg in evaluacion.preguntas:
        alt_elegida = respuestas_map.get(preg.id_pregunta)
        es_correcta = alt_elegida.es_correcta if alt_elegida else False
        correcta_real = next((a for a in preg.alternativas if a.es_correcta), None)

        desglose_preguntas.append(
            {
                "id_pregunta": preg.id_pregunta,
                "enunciado": preg.enunciado,
                "puntaje_posible": preg.puntaje,
                "puntaje_obtenido": preg.puntaje if es_correcta else 0.0,
                "es_correcta": es_correcta,
                "alternativa_seleccionada": {
                    "id_alternativa": alt_elegida.id_alternativa,
                    "texto": alt_elegida.texto,
                }
                if alt_elegida
                else None,
                "alternativa_correcta": {
                    "id_alternativa": correcta_real.id_alternativa,
                    "texto": correcta_real.texto,
                }
                if correcta_real
                else None,
            }
        )

    return (
        jsonify(
            {
                "exito": True,
                "tema": {
                    "id_tema": resultado_data["tema"].id_tema,
                    "titulo": resultado_data["tema"].titulo,
                },
                "resultado": {
                    "id_intento_evaluacion": intento.id_intento_evaluacion,
                    "puntaje_obtenido": intento.puntaje_obtenido,
                    "puntaje_minimo": evaluacion.puntaje_minimo,
                    "aprobado": intento.aprobado,
                    "fecha_intento": intento.fecha_intento.isoformat() if intento.fecha_intento else None,
                    "desglose": desglose_preguntas,
                },
            }
        ),
        200,
    )
