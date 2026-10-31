from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.core import (
    ActividadService,
    AprendizajeService,
    EvaluacionService,
    ProgresoService,
)

aprendizaje_bp = Blueprint("aprendizaje", __name__)


def _es_url_segura(target: str | None) -> bool:
    if not target:
        return False
    url = urlsplit(target)
    return not url.netloc and url.path.startswith("/") and not url.path.startswith("//")


@aprendizaje_bp.get("/temas")
def lista_temas():
    """Catálogo accesible de temas educativos disponibles con indicadores de progreso si hay sesión."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    temas, progreso_por_tema = AprendizajeService.obtener_catalogo_temas(id_usuario)

    return render_template(
        "aprendizaje/temas.html",
        temas=temas,
        progreso_por_tema=progreso_por_tema,
    )


@aprendizaje_bp.get("/temas/<int:id_tema>")
def detalle_tema(id_tema: int):
    """Detalle de un tema con la lista ordenada de sus lecciones e indicador de avance."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    detalle = AprendizajeService.obtener_detalle_tema(id_tema, id_usuario)
    if detalle is None:
        abort(404)

    return render_template("aprendizaje/tema_detalle.html", **detalle)


@aprendizaje_bp.get("/temas/<int:id_tema>/contenidos/<int:id_contenido>")
def ver_contenido(id_tema: int, id_contenido: int):
    """Lectura accesible de una lección educativa con navegación secuencial y estado de completado."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    lectura = AprendizajeService.obtener_contenido_lectura(id_tema, id_contenido, id_usuario)
    if lectura is None:
        abort(404)

    return render_template("aprendizaje/contenido.html", **lectura)


@aprendizaje_bp.post("/temas/<int:id_tema>/contenidos/<int:id_contenido>/completar")
@login_required
def marcar_completado(id_tema: int, id_contenido: int):
    """Registra una lección como completada por el usuario autenticado."""
    exito, titulo = AprendizajeService.actualizar_progreso_leccion(
        id_tema=id_tema,
        id_contenido=id_contenido,
        id_usuario=current_user.id_usuario,
        completado=True,
    )
    if not exito:
        abort(404)

    flash(f"¡Excelente avance! Marcaste «{titulo}» como completada.", "exito")

    destino = request.form.get("siguiente_url")
    if destino and _es_url_segura(destino):
        return redirect(destino)

    return redirect(
        url_for(
            "aprendizaje.ver_contenido",
            id_tema=id_tema,
            id_contenido=id_contenido,
        )
    )


@aprendizaje_bp.post("/temas/<int:id_tema>/contenidos/<int:id_contenido>/desmarcar")
@login_required
def desmarcar_completado(id_tema: int, id_contenido: int):
    """Permite desmarcar una lección para volver a estudiarla."""
    exito, titulo = AprendizajeService.actualizar_progreso_leccion(
        id_tema=id_tema,
        id_contenido=id_contenido,
        id_usuario=current_user.id_usuario,
        completado=False,
    )
    if not exito:
        abort(404)

    flash(f"Se actualizó la lección «{titulo}» como pendiente de estudio.", "info")
    return redirect(
        url_for(
            "aprendizaje.ver_contenido",
            id_tema=id_tema,
            id_contenido=id_contenido,
        )
    )


@aprendizaje_bp.get("/mi-progreso")
@login_required
def mi_progreso():
    """Panel de control del ciudadano con el resumen cuantitativo y el estado de sus módulos."""
    resumen = ProgresoService.obtener_resumen_progreso_usuario(current_user.id_usuario)
    return render_template("aprendizaje/mi_progreso.html", resumen=resumen)


@aprendizaje_bp.get("/temas/<int:id_tema>/actividades/<int:id_actividad>")
def ver_actividad(id_tema: int, id_actividad: int):
    """Muestra una actividad práctica o simulación interactiva con sus instrucciones y formulario."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    actividad_data = ActividadService.obtener_actividad_para_resolver(
        id_tema=id_tema,
        id_actividad=id_actividad,
        id_usuario=id_usuario,
    )
    if actividad_data is None:
        abort(404)

    return render_template("aprendizaje/actividad.html", **actividad_data)


@aprendizaje_bp.post("/temas/<int:id_tema>/actividades/<int:id_actividad>/resolver")
@login_required
def resolver_actividad(id_tema: int, id_actividad: int):
    """Evalúa la decisión del ciudadano en la actividad y registra el intento con retroalimentación."""
    opcion_id = request.form.get("opcion_id")
    exito, resultado_data, error_msg = ActividadService.procesar_resolucion_actividad(
        id_tema=id_tema,
        id_actividad=id_actividad,
        id_usuario=current_user.id_usuario,
        opcion_id=opcion_id,
    )

    if not exito:
        if error_msg and "tema" in error_msg.lower() or error_msg and "disponible" in error_msg.lower():
            abort(404)
        flash(error_msg or "Error al procesar la respuesta.", "error")
        return redirect(
            url_for(
                "aprendizaje.ver_actividad",
                id_tema=id_tema,
                id_actividad=id_actividad,
            )
        )

    if resultado_data["es_correcta"]:
        flash("¡Felicitaciones! Has completado la actividad con una decisión acertada.", "exito")
    else:
        flash("Atención: tu respuesta revela un riesgo de seguridad. Revisa la explicación detallada.", "error")

    return render_template("aprendizaje/actividad_resultado.html", **resultado_data)


@aprendizaje_bp.get("/temas/<int:id_tema>/evaluacion")
def ver_evaluacion(id_tema: int):
    """Presenta el cuestionario formal de evaluación del tema."""
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    eval_data = EvaluacionService.obtener_evaluacion_tema(id_tema, id_usuario)
    if eval_data is None:
        abort(404)

    return render_template("aprendizaje/evaluacion.html", **eval_data)


@aprendizaje_bp.post("/temas/<int:id_tema>/evaluacion/enviar")
@login_required
def enviar_evaluacion(id_tema: int):
    """Califica las respuestas del ciudadano y persiste el intento con sus respuestas."""
    exito, intento, error_msg = EvaluacionService.calificar_y_registrar_intento(
        id_tema=id_tema,
        id_usuario=current_user.id_usuario,
        form_data=request.form,
    )

    if not exito:
        if error_msg and "no existe" in error_msg.lower():
            abort(404)
        flash(error_msg or "Error al procesar la evaluación.", "error")
        return redirect(url_for("aprendizaje.ver_evaluacion", id_tema=id_tema))

    if intento.aprobado:
        flash(
            f"¡Felicitaciones! Aprobaste la evaluación con una nota de {intento.puntaje_obtenido:.1f} puntos.",
            "exito",
        )
    else:
        flash(
            f"Obtuviste {intento.puntaje_obtenido:.1f} puntos (mínimo aprobatorio: 14.0). Puedes repasar las lecciones y volver a intentarlo.",
            "error",
        )

    return redirect(
        url_for(
            "aprendizaje.resultado_evaluacion",
            id_tema=id_tema,
            id_intento=intento.id_intento_evaluacion,
        )
    )


@aprendizaje_bp.get("/temas/<int:id_tema>/evaluacion/resultado/<int:id_intento>")
@login_required
def resultado_evaluacion(id_tema: int, id_intento: int):
    """Muestra la retroalimentación detallada y el desglose de preguntas de un intento."""
    resultado_data = EvaluacionService.obtener_resultado_intento(
        id_tema=id_tema,
        id_intento=id_intento,
        id_usuario=current_user.id_usuario,
    )
    if resultado_data is None:
        abort(404)

    return render_template("aprendizaje/evaluacion_resultado.html", **resultado_data)
