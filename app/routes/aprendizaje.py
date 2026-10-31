from flask import Blueprint, abort, render_template
from sqlalchemy import select

from app.extensions import db
from app.models import Contenido, Tema

aprendizaje_bp = Blueprint("aprendizaje", __name__)


@aprendizaje_bp.get("/temas")
def lista_temas():
    """Catálogo accesible de temas educativos disponibles."""
    temas = db.session.scalars(
        select(Tema).where(Tema.estado == "publicado").order_by(Tema.orden)
    ).all()
    return render_template("aprendizaje/temas.html", temas=temas)


@aprendizaje_bp.get("/temas/<int:id_tema>")
def detalle_tema(id_tema: int):
    """Detalle de un tema con la lista ordenada de sus contenidos/lecciones."""
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

    return render_template(
        "aprendizaje/tema_detalle.html",
        tema=tema,
        contenidos=contenidos,
    )


@aprendizaje_bp.get("/temas/<int:id_tema>/contenidos/<int:id_contenido>")
def ver_contenido(id_tema: int, id_contenido: int):
    """Lectura accesible de una lección educativa con navegación secuencial."""
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

    return render_template(
        "aprendizaje/contenido.html",
        tema=tema,
        contenido=contenido,
        parrafos=parrafos,
        indice=indice_actual + 1,
        total_lecciones=len(lecciones),
        anterior=anterior,
        siguiente=siguiente,
    )
