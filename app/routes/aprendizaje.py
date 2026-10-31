from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.extensions import db
from app.models import Contenido, ProgresoContenido, Tema

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

    return render_template(
        "aprendizaje/tema_detalle.html",
        tema=tema,
        contenidos=contenidos,
        completados_ids=completados_ids,
        progreso_tema=progreso_tema,
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
