from flask import render_template, url_for
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
    paso_siguiente = None

    if current_user.is_authenticated:
        resumen = ProgresoService.obtener_resumen_progreso_usuario(current_user.id_usuario)
        for item in resumen.get("temas", []):
            if item.get("siguiente_leccion"):
                siguiente_leccion = item["siguiente_leccion"]
                tema_siguiente = item["tema"]
                break
            elif item.get("siguiente_paso"):
                sp = item["siguiente_paso"]
                tema_obj = item["tema"]
                if sp["tipo"] == "actividad":
                    paso_siguiente = {
                        "tipo": "actividad",
                        "url": url_for("aprendizaje.detalle_tema", id_tema=tema_obj.id_tema) + "#titulo-actividades",
                        "texto_accion": f"Realizar taller de «{tema_obj.titulo}»",
                    }
                    tema_siguiente = tema_obj
                    break
                elif sp["tipo"] == "evaluacion":
                    paso_siguiente = {
                        "tipo": "evaluacion",
                        "url": url_for("aprendizaje.ver_evaluacion", id_tema=tema_obj.id_tema),
                        "texto_accion": f"Rendir evaluación de «{tema_obj.titulo}»",
                    }
                    tema_siguiente = tema_obj
                    break

    return render_template(
        "index.html",
        temas=temas,
        progreso_por_tema=progreso_por_tema,
        resumen=resumen,
        siguiente_leccion=siguiente_leccion,
        tema_siguiente=tema_siguiente,
        paso_siguiente=paso_siguiente,
    )
