"""Endpoints del catálogo de temas educativos y lecciones en la API REST v1."""

from flask import jsonify, request
from flask_login import current_user

from app.core import AprendizajeService, api_login_required
from app.routes.api.v1 import api_v1_bp


@api_v1_bp.get("/temas")
def api_lista_temas():
    """Retorna el catálogo ordenado de temas educativos publicados con indicadores de avance."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    temas, progreso_por_tema = AprendizajeService.obtener_catalogo_temas(id_usuario)

    datos = []
    for tema in temas:
        lecciones_pub = [c for c in tema.contenidos if c.estado == "publicado"]
        item = {
            "id_tema": tema.id_tema,
            "titulo": tema.titulo,
            "descripcion": tema.descripcion,
            "orden": tema.orden,
            "estado": tema.estado,
            "total_lecciones": len(lecciones_pub),
            "progreso": progreso_por_tema.get(tema.id_tema) if id_usuario else None,
        }
        datos.append(item)

    return (
        jsonify(
            {
                "exito": True,
                "total": len(datos),
                "temas": datos,
            }
        ),
        200,
    )


@api_v1_bp.get("/temas/<int:id_tema>")
def api_detalle_tema(id_tema: int):
    """Retorna el detalle completo de un tema, incluyendo lecciones, actividades y evaluación."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    detalle = AprendizajeService.obtener_detalle_tema(id_tema, id_usuario)

    if detalle is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "El tema solicitado no existe o no está publicado.",
                    "codigo": "tema_no_encontrado",
                }
            ),
            404,
        )

    tema = detalle["tema"]
    contenidos = [
        {
            "id_contenido": c.id_contenido,
            "titulo": c.titulo,
            "orden": c.orden,
            "completada": c.id_contenido in detalle["completados_ids"],
        }
        for c in detalle["contenidos"]
    ]

    actividades = [
        {
            "id_actividad": a.id_actividad,
            "titulo": a.titulo,
            "tipo": a.tipo,
            "resuelto": detalle["intentos_actividades"].get(a.id_actividad) is not None,
            "ultimo_resultado": getattr(
                detalle["intentos_actividades"].get(a.id_actividad), "resultado", None
            ),
        }
        for a in detalle["actividades"]
    ]

    eval_data = None
    if detalle["evaluacion"]:
        ev = detalle["evaluacion"]
        mejor = detalle["mejor_intento_eval"]
        eval_data = {
            "id_evaluacion": ev.id_evaluacion,
            "titulo": ev.titulo,
            "puntaje_minimo": ev.puntaje_minimo,
            "puntaje_maximo": ev.puntaje_maximo,
            "total_preguntas": len(ev.preguntas),
            "aprobado": mejor.puntaje_obtenido >= ev.puntaje_minimo if mejor else False,
            "mejor_puntaje": mejor.puntaje_obtenido if mejor else None,
        }

    return (
        jsonify(
            {
                "exito": True,
                "tema": {
                    "id_tema": tema.id_tema,
                    "titulo": tema.titulo,
                    "descripcion": tema.descripcion,
                    "orden": tema.orden,
                    "progreso": detalle["progreso_tema"],
                    "contenidos": contenidos,
                    "actividades": actividades,
                    "evaluacion": eval_data,
                },
            }
        ),
        200,
    )


@api_v1_bp.get("/temas/<int:id_tema>/contenidos/<int:id_contenido>")
def api_ver_contenido(id_tema: int, id_contenido: int):
    """Retorna la lección educativa con sus párrafos, navegación secuencial y estado formativo."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    lectura = AprendizajeService.obtener_contenido_lectura(id_tema, id_contenido, id_usuario)

    if lectura is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "La lección solicitada no existe o no se encuentra disponible.",
                    "codigo": "contenido_no_encontrado",
                }
            ),
            404,
        )

    anterior = lectura["anterior"]
    siguiente = lectura["siguiente"]

    return (
        jsonify(
            {
                "exito": True,
                "tema": {
                    "id_tema": lectura["tema"].id_tema,
                    "titulo": lectura["tema"].titulo,
                },
                "contenido": {
                    "id_contenido": lectura["contenido"].id_contenido,
                    "titulo": lectura["contenido"].titulo,
                    "texto_completo": lectura["contenido"].contenido,
                    "parrafos": lectura["parrafos"],
                    "orden": lectura["contenido"].orden,
                    "indice": lectura["indice"],
                    "total_lecciones": lectura["total_lecciones"],
                    "esta_completada": lectura["esta_completada"],
                    "fecha_completado": lectura["fecha_completado"].isoformat()
                    if lectura["fecha_completado"]
                    else None,
                },
                "navegacion": {
                    "anterior": {
                        "id_contenido": anterior.id_contenido,
                        "titulo": anterior.titulo,
                    }
                    if anterior
                    else None,
                    "siguiente": {
                        "id_contenido": siguiente.id_contenido,
                        "titulo": siguiente.titulo,
                    }
                    if siguiente
                    else None,
                },
            }
        ),
        200,
    )


@api_v1_bp.post("/temas/<int:id_tema>/contenidos/<int:id_contenido>/completar")
@api_login_required
def api_marcar_contenido(id_tema: int, id_contenido: int):
    """Permite marcar o desmarcar una lección formativa como completada."""
    data = request.get_json(silent=True) or {}
    completado = bool(data.get("completado", True))

    exito, titulo = AprendizajeService.actualizar_progreso_leccion(
        id_tema=id_tema,
        id_contenido=id_contenido,
        id_usuario=current_user.id_usuario,
        completado=completado,
    )

    if not exito:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "No se pudo actualizar el progreso: lección o tema inexistente.",
                    "codigo": "leccion_no_encontrada",
                }
            ),
            404,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Lección '{titulo}' marcada como {'completada' if completado else 'pendiente'}.",
                "id_tema": id_tema,
                "id_contenido": id_contenido,
                "completado": completado,
            }
        ),
        200,
    )
