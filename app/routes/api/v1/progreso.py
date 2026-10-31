"""Endpoints de consulta de progreso y seguimiento formativo en la API REST v1."""

from flask import jsonify
from flask_login import current_user

from app.core import ProgresoService, api_login_required
from app.routes.api.v1 import api_v1_bp


@api_v1_bp.get("/progreso/mi-progreso")
@api_login_required
def api_mi_progreso():
    """Retorna el panel cuantitativo y estado de avance de los módulos del ciudadano autenticado."""
    resumen = ProgresoService.obtener_resumen_progreso_usuario(current_user.id_usuario)

    temas_serializados = []
    for t in resumen.get("temas", []):
        tema_obj = t["tema"]
        eval_info = t.get("evaluacion_info")
        temas_serializados.append(
            {
                "id_tema": tema_obj.id_tema,
                "titulo": tema_obj.titulo,
                "orden": tema_obj.orden,
                "estado": t["estado"],
                "porcentaje": t["porcentaje"],
                "total_lecciones": t["total_lecciones"],
                "lecciones_completadas": t["lecciones_completadas"],
                "total_actividades": t["total_actividades"],
                "actividades_completadas": t["actividades_completadas"],
                "evaluacion": {
                    "id_evaluacion": eval_info["evaluacion"].id_evaluacion,
                    "titulo": eval_info["evaluacion"].titulo,
                    "aprobado": eval_info["aprobado"],
                    "mejor_puntaje": eval_info["mejor_intento"].puntaje_obtenido
                    if eval_info["mejor_intento"]
                    else None,
                }
                if eval_info
                else None,
                "siguiente_leccion": {
                    "id_contenido": t["siguiente_leccion"].id_contenido,
                    "titulo": t["siguiente_leccion"].titulo,
                }
                if t.get("siguiente_leccion")
                else None,
            }
        )

    return (
        jsonify(
            {
                "exito": True,
                "resumen": {
                    "total_lecciones": resumen["total_lecciones"],
                    "lecciones_completadas": resumen["lecciones_completadas"],
                    "total_actividades": resumen["total_actividades"],
                    "actividades_completadas": resumen["actividades_completadas"],
                    "total_evaluaciones": resumen["total_evaluaciones"],
                    "evaluaciones_aprobadas": resumen["evaluaciones_aprobadas"],
                    "porcentaje_global": resumen["porcentaje_global"],
                    "total_temas": resumen["total_temas"],
                    "temas_completados": resumen["temas_completados"],
                    "temas": temas_serializados,
                },
            }
        ),
        200,
    )
