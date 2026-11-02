from flask import render_template
from flask_login import current_user

from app.core import AprendizajeService, ProgresoService
from app.routes import main_bp


@main_bp.get("/")
def index():
    id_usuario = current_user.id_usuario if current_user.is_authenticated else None
    temas, progreso_por_tema = AprendizajeService.obtener_catalogo_temas(id_usuario)

    resumen = None
    siguiente_leccion = None
    tema_siguiente = None

    if current_user.is_authenticated:
        resumen = ProgresoService.obtener_resumen_progreso_usuario(current_user.id_usuario)
        for item in resumen.get("temas", []):
            if item.get("siguiente_leccion"):
                siguiente_leccion = item["siguiente_leccion"]
                tema_siguiente = item["tema"]
                break

    return render_template(
        "index.html",
        temas=temas,
        progreso_por_tema=progreso_por_tema,
        resumen=resumen,
        siguiente_leccion=siguiente_leccion,
        tema_siguiente=tema_siguiente,
    )
