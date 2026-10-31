from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    Actividad,
    Alternativa,
    Contenido,
    Evaluacion,
    IntentoActividad,
    IntentoEvaluacion,
    Pregunta,
    ProgresoContenido,
    Respuesta,
    Tema,
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
    temas = db.session.scalars(
        select(Tema).where(Tema.estado == "publicado").order_by(Tema.orden)
    ).all()

    progreso_por_tema = {}
    if current_user.is_authenticated:
        completados = ProgresoContenido.obtener_completados_usuario(current_user.id_usuario)
        for tema in temas:
            lecciones_pub = [c for c in tema.contenidos if c.estado == "publicado"]
            total = len(lecciones_pub)
            completadas = sum(1 for c in lecciones_pub if c.id_contenido in completados)
            pct = round((completadas / total) * 100) if total > 0 else 0
            progreso_por_tema[tema.id_tema] = {
                "total": total,
                "completadas": completadas,
                "porcentaje": pct,
                "completado": completadas == total and total > 0,
            }

    return render_template(
        "aprendizaje/temas.html",
        temas=temas,
        progreso_por_tema=progreso_por_tema,
    )


@aprendizaje_bp.get("/temas/<int:id_tema>")
def detalle_tema(id_tema: int):
    """Detalle de un tema con la lista ordenada de sus lecciones e indicador de avance."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    contenidos = db.session.scalars(
        select(Contenido)
        .where(Contenido.id_tema == tema.id_tema, Contenido.estado == "publicado")
        .order_by(Contenido.orden)
    ).all()

    completados_ids: set[int] = set()
    progreso_tema = None
    if current_user.is_authenticated:
        completados_ids = ProgresoContenido.obtener_completados_usuario(
            current_user.id_usuario, [c.id_contenido for c in contenidos]
        )
        total = len(contenidos)
        completadas = len(completados_ids)
        pct = round((completadas / total) * 100) if total > 0 else 0
        progreso_tema = {
            "total": total,
            "completadas": completadas,
            "porcentaje": pct,
            "completado": completadas == total and total > 0,
        }

    actividades = db.session.scalars(
        select(Actividad)
        .where(Actividad.id_tema == tema.id_tema, Actividad.estado == "publicado")
    ).all()

    intentos_actividades = {}
    if current_user.is_authenticated:
        for act in actividades:
            intentos_actividades[act.id_actividad] = act.obtener_ultimo_intento(
                current_user.id_usuario
            )

    evaluacion = db.session.scalar(
        select(Evaluacion)
        .where(Evaluacion.id_tema == tema.id_tema, Evaluacion.estado == "publicado")
        .options(selectinload(Evaluacion.preguntas))
    )

    mejor_intento_eval = None
    ultimo_intento_eval = None
    if evaluacion and current_user.is_authenticated:
        mejor_intento_eval = evaluacion.obtener_mejor_intento(current_user.id_usuario)
        ultimo_intento_eval = evaluacion.obtener_ultimo_intento(current_user.id_usuario)

    return render_template(
        "aprendizaje/tema_detalle.html",
        tema=tema,
        contenidos=contenidos,
        completados_ids=completados_ids,
        progreso_tema=progreso_tema,
        actividades=actividades,
        intentos_actividades=intentos_actividades,
        evaluacion=evaluacion,
        mejor_intento_eval=mejor_intento_eval,
        ultimo_intento_eval=ultimo_intento_eval,
    )


@aprendizaje_bp.get("/temas/<int:id_tema>/contenidos/<int:id_contenido>")
def ver_contenido(id_tema: int, id_contenido: int):
    """Lectura accesible de una lección educativa con navegación secuencial y estado de completado."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    contenido = db.session.scalar(
        select(Contenido).where(
            Contenido.id_contenido == id_contenido,
            Contenido.id_tema == tema.id_tema,
            Contenido.estado == "publicado",
        )
    )
    if contenido is None:
        abort(404)

    lecciones = db.session.scalars(
        select(Contenido)
        .where(Contenido.id_tema == tema.id_tema, Contenido.estado == "publicado")
        .order_by(Contenido.orden)
    ).all()

    indice_actual = next(
        (i for i, c in enumerate(lecciones) if c.id_contenido == contenido.id_contenido),
        -1,
    )

    anterior = lecciones[indice_actual - 1] if indice_actual > 0 else None
    siguiente = (
        lecciones[indice_actual + 1]
        if 0 <= indice_actual < len(lecciones) - 1
        else None
    )

    # Dividir el texto en párrafos para estructuración semántica HTML
    parrafos = [p.strip() for p in contenido.contenido.split("\n\n") if p.strip()]

    esta_completada = False
    fecha_completado = None
    if current_user.is_authenticated:
        progreso = db.session.scalar(
            select(ProgresoContenido).where(
                ProgresoContenido.id_usuario == current_user.id_usuario,
                ProgresoContenido.id_contenido == contenido.id_contenido,
            )
        )
        if progreso and progreso.completado:
            esta_completada = True
            fecha_completado = progreso.fecha_completado

    return render_template(
        "aprendizaje/contenido.html",
        tema=tema,
        contenido=contenido,
        parrafos=parrafos,
        indice=indice_actual + 1,
        total_lecciones=len(lecciones),
        anterior=anterior,
        siguiente=siguiente,
        esta_completada=esta_completada,
        fecha_completado=fecha_completado,
    )


@aprendizaje_bp.post("/temas/<int:id_tema>/contenidos/<int:id_contenido>/completar")
@login_required
def marcar_completado(id_tema: int, id_contenido: int):
    """Registra una lección como completada por el usuario autenticado."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    contenido = db.session.scalar(
        select(Contenido).where(
            Contenido.id_contenido == id_contenido,
            Contenido.id_tema == tema.id_tema,
            Contenido.estado == "publicado",
        )
    )
    if contenido is None:
        abort(404)

    ProgresoContenido.marcar_completado(
        id_usuario=current_user.id_usuario,
        id_contenido=contenido.id_contenido,
        completado=True,
    )
    flash(f"¡Excelente avance! Marcaste «{contenido.titulo}» como completada.", "exito")

    destino = request.form.get("siguiente_url")
    if destino and _es_url_segura(destino):
        return redirect(destino)

    return redirect(
        url_for(
            "aprendizaje.ver_contenido",
            id_tema=tema.id_tema,
            id_contenido=contenido.id_contenido,
        )
    )


@aprendizaje_bp.post("/temas/<int:id_tema>/contenidos/<int:id_contenido>/desmarcar")
@login_required
def desmarcar_completado(id_tema: int, id_contenido: int):
    """Permite desmarcar una lección para volver a estudiarla."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    contenido = db.session.scalar(
        select(Contenido).where(
            Contenido.id_contenido == id_contenido,
            Contenido.id_tema == tema.id_tema,
            Contenido.estado == "publicado",
        )
    )
    if contenido is None:
        abort(404)

    ProgresoContenido.marcar_completado(
        id_usuario=current_user.id_usuario,
        id_contenido=contenido.id_contenido,
        completado=False,
    )
    flash(f"Se actualizó la lección «{contenido.titulo}» a pendiente de estudio.", "info")

    return redirect(
        url_for(
            "aprendizaje.ver_contenido",
            id_tema=tema.id_tema,
            id_contenido=contenido.id_contenido,
        )
    )


@aprendizaje_bp.get("/mi-progreso")
@login_required
def mi_progreso():
    """Panel de avance formativo del ciudadano."""
    resumen = ProgresoContenido.obtener_resumen_progreso_usuario(current_user.id_usuario)
    return render_template("aprendizaje/mi_progreso.html", resumen=resumen)


@aprendizaje_bp.get("/temas/<int:id_tema>/actividades/<int:id_actividad>")
def ver_actividad(id_tema: int, id_actividad: int):
    """Presenta una actividad práctica o simulación en entorno seguro."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    actividad = db.session.scalar(
        select(Actividad).where(
            Actividad.id_actividad == id_actividad,
            Actividad.id_tema == tema.id_tema,
            Actividad.estado == "publicado",
        )
    )
    if actividad is None:
        abort(404)

    ultimo_intento = None
    if current_user.is_authenticated:
        ultimo_intento = actividad.obtener_ultimo_intento(current_user.id_usuario)

    return render_template(
        "aprendizaje/actividad.html",
        tema=tema,
        actividad=actividad,
        configuracion=actividad.configuracion,
        ultimo_intento=ultimo_intento,
    )


@aprendizaje_bp.post("/temas/<int:id_tema>/actividades/<int:id_actividad>/resolver")
@login_required
def resolver_actividad(id_tema: int, id_actividad: int):
    """Evalúa la decisión del ciudadano en la actividad y registra el intento con retroalimentación."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    actividad = db.session.scalar(
        select(Actividad).where(
            Actividad.id_actividad == id_actividad,
            Actividad.id_tema == tema.id_tema,
            Actividad.estado == "publicado",
        )
    )
    if actividad is None:
        abort(404)

    opcion_id = request.form.get("opcion_id")
    config = actividad.configuracion
    opciones = config.get("opciones", [])

    opcion_elegida = next((o for o in opciones if o.get("id") == opcion_id), None)
    if opcion_elegida is None:
        flash("Por favor, selecciona una alternativa antes de enviar tu respuesta.", "error")
        return redirect(
            url_for(
                "aprendizaje.ver_actividad",
                id_tema=tema.id_tema,
                id_actividad=actividad.id_actividad,
            )
        )

    es_correcta = bool(opcion_elegida.get("es_correcta"))
    resultado_clave = "exitoso" if es_correcta else "requiere_repaso"

    intento = IntentoActividad.registrar(
        id_usuario=current_user.id_usuario,
        id_actividad=actividad.id_actividad,
        resultado=resultado_clave,
    )

    if es_correcta:
        flash("¡Felicitaciones! Has completado la actividad con una decisión acertada.", "exito")
    else:
        flash("Atención: tu respuesta revela un riesgo de seguridad. Revisa la explicación detallada.", "error")

    return render_template(
        "aprendizaje/actividad_resultado.html",
        tema=tema,
        actividad=actividad,
        configuracion=config,
        opcion_elegida=opcion_elegida,
        es_correcta=es_correcta,
        intento=intento,
    )


@aprendizaje_bp.get("/temas/<int:id_tema>/evaluacion")
def ver_evaluacion(id_tema: int):
    """Presenta el cuestionario formal de evaluación del tema."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    evaluacion = db.session.scalar(
        select(Evaluacion)
        .where(Evaluacion.id_tema == tema.id_tema, Evaluacion.estado == "publicado")
        .options(
            selectinload(Evaluacion.preguntas).selectinload(Pregunta.alternativas)
        )
    )
    if evaluacion is None:
        abort(404)

    mejor_intento = None
    ultimo_intento = None
    if current_user.is_authenticated:
        mejor_intento = evaluacion.obtener_mejor_intento(current_user.id_usuario)
        ultimo_intento = evaluacion.obtener_ultimo_intento(current_user.id_usuario)

    return render_template(
        "aprendizaje/evaluacion.html",
        tema=tema,
        evaluacion=evaluacion,
        mejor_intento=mejor_intento,
        ultimo_intento=ultimo_intento,
    )


@aprendizaje_bp.post("/temas/<int:id_tema>/evaluacion/enviar")
@login_required
def enviar_evaluacion(id_tema: int):
    """Califica las respuestas del ciudadano y persiste el intento con sus respuestas."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    evaluacion = db.session.scalar(
        select(Evaluacion)
        .where(Evaluacion.id_tema == tema.id_tema, Evaluacion.estado == "publicado")
        .options(
            selectinload(Evaluacion.preguntas).selectinload(Pregunta.alternativas)
        )
    )
    if evaluacion is None:
        abort(404)

    # Validar que se hayan respondido todas las preguntas
    respuestas_dict = {}
    faltan_preguntas = False

    for pregunta in evaluacion.preguntas:
        nombre_campo = f"pregunta_{pregunta.id_pregunta}"
        valor_alt = request.form.get(nombre_campo)
        if not valor_alt or not valor_alt.isdigit():
            faltan_preguntas = True
            break
        respuestas_dict[pregunta.id_pregunta] = int(valor_alt)

    if faltan_preguntas or len(respuestas_dict) != len(evaluacion.preguntas):
        flash(
            "Por favor, responde todas las preguntas del cuestionario antes de enviar tu evaluación.",
            "error",
        )
        return redirect(url_for("aprendizaje.ver_evaluacion", id_tema=tema.id_tema))

    try:
        intento = IntentoEvaluacion.registrar_intento(
            id_usuario=current_user.id_usuario,
            evaluacion=evaluacion,
            respuestas_dict=respuestas_dict,
        )
    except ValueError as e:
        flash(f"Error de validación al procesar las respuestas: {e}", "error")
        return redirect(url_for("aprendizaje.ver_evaluacion", id_tema=tema.id_tema))

    if intento.aprobado:
        flash(
            f"¡Felicitaciones! Aprobaste la evaluación con una nota de {intento.puntaje_obtenido:.1f} puntos.",
            "exito",
        )
    else:
        flash(
            f"Obtuviste {intento.puntaje_obtenido:.1f} puntos (mínimo aprobatorio: {evaluacion.puntaje_minimo:.1f}). Puedes repasar las lecciones y volver a intentarlo.",
            "error",
        )

    return redirect(
        url_for(
            "aprendizaje.resultado_evaluacion",
            id_tema=tema.id_tema,
            id_intento=intento.id_intento_evaluacion,
        )
    )


@aprendizaje_bp.get("/temas/<int:id_tema>/evaluacion/resultado/<int:id_intento>")
@login_required
def resultado_evaluacion(id_tema: int, id_intento: int):
    """Muestra la retroalimentación detallada y el desglose de preguntas de un intento."""
    tema = db.session.scalar(
        select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
    )
    if tema is None:
        abort(404)

    intento = db.session.scalar(
        select(IntentoEvaluacion)
        .where(
            IntentoEvaluacion.id_intento_evaluacion == id_intento,
            IntentoEvaluacion.id_usuario == current_user.id_usuario,
        )
        .options(
            selectinload(IntentoEvaluacion.evaluacion)
            .selectinload(Evaluacion.preguntas)
            .selectinload(Pregunta.alternativas),
            selectinload(IntentoEvaluacion.respuestas).selectinload(Respuesta.alternativa),
        )
    )
    if intento is None or intento.evaluacion.id_tema != tema.id_tema:
        abort(404)

    respuestas_por_pregunta = {r.id_pregunta: r.alternativa for r in intento.respuestas}

    return render_template(
        "aprendizaje/evaluacion_resultado.html",
        tema=tema,
        evaluacion=intento.evaluacion,
        intento=intento,
        respuestas_por_pregunta=respuestas_por_pregunta,
    )
