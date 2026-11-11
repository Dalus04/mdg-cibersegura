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
    temas_prioritarios = temas[:3]

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

        # Selección curada de hasta 3 módulos prioritarios para la portada autenticada
        items_resumen = resumen.get("temas", [])
        activos = []
        completados = []
        pendientes = []
        for item in items_resumen:
            hay_avance = (
                item["lecciones_completadas"] > 0
                or item["actividades_intentadas"] > 0
                or (item["evaluacion_info"] and item["evaluacion_info"]["mejor_intento"] is not None)
            )
            estado_mod = item["estado_modulo"]
            if estado_mod == "completado":
                completados.append(item["tema"])
            elif hay_avance and estado_mod in ("en_progreso", "evaluacion_pendiente", "evaluacion_desaprobada"):
                activos.append(item["tema"])
            else:
                pendientes.append(item["tema"])

        seleccion = []
        for t in activos[:2]:
            seleccion.append(t)
        if completados and len(seleccion) < 3:
            seleccion.append(completados[-1])
        for t in pendientes:
            if len(seleccion) >= 3:
                break
            if t not in seleccion:
                seleccion.append(t)
        for t in activos[2:] + completados[:-1]:
            if len(seleccion) >= 3:
                break
            if t not in seleccion:
                seleccion.append(t)

        temas_prioritarios = sorted(seleccion, key=lambda x: x.orden)

    return render_template(
        "index.html",
        temas=temas,
        temas_prioritarios=temas_prioritarios,
        progreso_por_tema=progreso_por_tema,
        resumen=resumen,
        siguiente_leccion=siguiente_leccion,
        tema_siguiente=tema_siguiente,
        paso_siguiente=paso_siguiente,
    )
