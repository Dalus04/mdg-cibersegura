"""Controlador Web para el Módulo de Administración de MDG Cibersegura (Fase 5)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.core import AdminService, admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
@admin_required
def dashboard():
    """Panel ejecutivo principal con los indicadores de desempeño institucional y accesos rápidos."""
    metricas = AdminService.obtener_metricas_generales()
    return render_template("admin/dashboard.html", metricas=metricas)


@admin_bp.get("/usuarios")
@admin_required
def usuarios():
    """Consola accesible para la supervisión y gestión de cuentas de usuarios."""
    busqueda = request.args.get("busqueda", "").strip()
    rol_filtro = request.args.get("rol", "").strip()
    estado_filtro = request.args.get("estado", "").strip()

    lista_usuarios = AdminService.listar_usuarios(
        busqueda=busqueda or None,
        rol_filtro=rol_filtro or None,
        estado_filtro=estado_filtro or None,
    )
    return render_template(
        "admin/usuarios.html",
        usuarios=lista_usuarios,
        busqueda=busqueda,
        rol_filtro=rol_filtro,
        estado_filtro=estado_filtro,
    )


@admin_bp.post("/usuarios/<int:id_usuario>/estado")
@admin_required
def cambiar_estado_usuario(id_usuario: int):
    """Acción protegida para activar o desactivar la cuenta de un usuario."""
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        flash("Debe especificar un estado válido.", "error")
        return redirect(url_for("admin.usuarios"))

    exito, error_msg = AdminService.actualizar_estado_usuario(
        id_usuario=id_usuario,
        nuevo_estado=nuevo_estado,
        id_solicitante=current_user.id_usuario,
    )
    if not exito:
        flash(error_msg or "No se pudo actualizar el usuario.", "error")
    else:
        flash(f"Estado del usuario actualizado a '{nuevo_estado}' con éxito.", "exito")

    return redirect(url_for("admin.usuarios"))


@admin_bp.get("/contenidos")
@admin_required
def contenidos():
    """Gestión de temas educativos y lecciones institucionales."""
    lista_temas = AdminService.listar_contenidos_admin()
    return render_template("admin/contenidos.html", temas=lista_temas)


@admin_bp.post("/temas/<int:id_tema>/estado")
@admin_required
def cambiar_estado_tema(id_tema: int):
    """Modifica el estado de publicación de un tema institucional."""
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        flash("Estado de tema no válido.", "error")
        return redirect(url_for("admin.contenidos"))

    exito, error_msg = AdminService.actualizar_estado_tema(id_tema=id_tema, nuevo_estado=nuevo_estado)
    if not exito:
        flash(error_msg or "Error al actualizar estado del tema.", "error")
    else:
        flash(f"Estado del tema actualizado a '{nuevo_estado}'.", "exito")

    return redirect(url_for("admin.contenidos"))


@admin_bp.post("/contenidos/<int:id_contenido>/estado")
@admin_required
def cambiar_estado_contenido(id_contenido: int):
    """Modifica el estado de una lección formativa."""
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        flash("Estado de lección no válido.", "error")
        return redirect(url_for("admin.contenidos"))

    exito, error_msg = AdminService.actualizar_estado_contenido(
        id_contenido=id_contenido, nuevo_estado=nuevo_estado
    )
    if not exito:
        flash(error_msg or "Error al actualizar la lección.", "error")
    else:
        flash(f"Estado de la lección actualizado a '{nuevo_estado}'.", "exito")

    return redirect(url_for("admin.contenidos"))


@admin_bp.get("/actividades")
@admin_required
def actividades():
    """Consola de supervisión de talleres prácticos y simulaciones de riesgos."""
    lista_actividades = AdminService.listar_actividades_admin()
    return render_template("admin/actividades.html", actividades=lista_actividades)


@admin_bp.post("/actividades/<int:id_actividad>/estado")
@admin_required
def cambiar_estado_actividad(id_actividad: int):
    """Modifica el estado de una actividad o simulación."""
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        flash("Estado de actividad no válido.", "error")
        return redirect(url_for("admin.actividades"))

    exito, error_msg = AdminService.actualizar_estado_actividad(
        id_actividad=id_actividad, nuevo_estado=nuevo_estado
    )
    if not exito:
        flash(error_msg or "Error al actualizar la actividad.", "error")
    else:
        flash(f"Estado de la actividad actualizado a '{nuevo_estado}'.", "exito")

    return redirect(url_for("admin.actividades"))


@admin_bp.get("/evaluaciones")
@admin_required
def evaluaciones():
    """Consola de métricas de cuestionarios formales de evaluación."""
    lista_evaluaciones = AdminService.listar_evaluaciones_admin()
    return render_template("admin/evaluaciones.html", evaluaciones=lista_evaluaciones)


@admin_bp.post("/evaluaciones/<int:id_evaluacion>/estado")
@admin_required
def cambiar_estado_evaluacion(id_evaluacion: int):
    """Modifica el estado de una evaluación formal."""
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        flash("Estado de evaluación no válido.", "error")
        return redirect(url_for("admin.evaluaciones"))

    exito, error_msg = AdminService.actualizar_estado_evaluacion(
        id_evaluacion=id_evaluacion, nuevo_estado=nuevo_estado
    )
    if not exito:
        flash(error_msg or "Error al actualizar la evaluación.", "error")
    else:
        flash(f"Estado de la evaluación actualizado a '{nuevo_estado}'.", "exito")

    return redirect(url_for("admin.evaluaciones"))
