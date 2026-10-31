"""Endpoints administrativos y analíticos protegidos en la API REST v1."""

from flask import jsonify, request
from flask_login import current_user

from app.core import AdminService, admin_required
from app.routes.api.v1 import api_v1_bp


@api_v1_bp.get("/admin/metricas")
@admin_required
def api_admin_metricas():
    """Retorna los indicadores cuantitativos institucionales consolidados."""
    metricas = AdminService.obtener_metricas_generales()
    return jsonify({"exito": True, "metricas": metricas}), 200


@api_v1_bp.get("/admin/usuarios")
@admin_required
def api_admin_usuarios():
    """Retorna la lista de usuarios con filtros opcionales de búsqueda, rol y estado."""
    busqueda = request.args.get("busqueda")
    rol_filtro = request.args.get("rol")
    estado_filtro = request.args.get("estado")

    usuarios = AdminService.listar_usuarios(
        busqueda=busqueda,
        rol_filtro=rol_filtro,
        estado_filtro=estado_filtro,
    )
    return jsonify({"exito": True, "total": len(usuarios), "usuarios": usuarios}), 200


@api_v1_bp.get("/admin/usuarios/<int:id_usuario>")
@admin_required
def api_admin_usuario_detalle(id_usuario: int):
    """Retorna el historial completo de progresos e intentos de un usuario."""
    usuario_det = AdminService.obtener_usuario_detalle(id_usuario)
    if usuario_det is None:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "El usuario solicitado no fue encontrado.",
                    "codigo": "usuario_no_encontrado",
                }
            ),
            404,
        )
    return jsonify({"exito": True, "usuario": usuario_det}), 200


@api_v1_bp.patch("/admin/usuarios/<int:id_usuario>/estado")
@admin_required
def api_admin_cambiar_estado_usuario(id_usuario: int):
    """Actualiza el estado de un usuario (activo o inactivo)."""
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe especificar el campo 'estado' ('activo' o 'inactivo').",
                    "codigo": "estado_requerido",
                }
            ),
            400,
        )

    exito, error_msg = AdminService.actualizar_estado_usuario(
        id_usuario=id_usuario,
        nuevo_estado=str(nuevo_estado),
        id_solicitante=current_user.id_usuario,
    )

    if not exito:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al actualizar el estado del usuario.",
                    "codigo": "error_actualizacion",
                }
            ),
            400,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Estado del usuario {id_usuario} actualizado a '{nuevo_estado}'.",
                "id_usuario": id_usuario,
                "estado": nuevo_estado,
            }
        ),
        200,
    )


@api_v1_bp.get("/admin/contenidos")
@admin_required
def api_admin_contenidos():
    """Retorna todos los temas y contenidos registrados en el sistema."""
    contenidos = AdminService.listar_contenidos_admin()
    return jsonify({"exito": True, "total_temas": len(contenidos), "temas": contenidos}), 200


@api_v1_bp.patch("/admin/temas/<int:id_tema>/estado")
@admin_required
def api_admin_cambiar_estado_tema(id_tema: int):
    """Modifica el estado de publicación de un tema."""
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe especificar el campo 'estado' ('publicado', 'borrador', 'desactivado').",
                    "codigo": "estado_requerido",
                }
            ),
            400,
        )

    exito, error_msg = AdminService.actualizar_estado_tema(id_tema=id_tema, nuevo_estado=str(nuevo_estado))
    if not exito:
        status_code = 404 if "no existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al actualizar estado del tema.",
                    "codigo": "error_actualizacion",
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Estado del tema {id_tema} actualizado a '{nuevo_estado}'.",
                "id_tema": id_tema,
                "estado": nuevo_estado,
            }
        ),
        200,
    )


@api_v1_bp.patch("/admin/contenidos/<int:id_contenido>/estado")
@admin_required
def api_admin_cambiar_estado_contenido(id_contenido: int):
    """Modifica el estado de publicación de una lección individual."""
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe especificar el campo 'estado' ('publicado', 'borrador', 'desactivado').",
                    "codigo": "estado_requerido",
                }
            ),
            400,
        )

    exito, error_msg = AdminService.actualizar_estado_contenido(
        id_contenido=id_contenido, nuevo_estado=str(nuevo_estado)
    )
    if not exito:
        status_code = 404 if "no existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al actualizar estado del contenido.",
                    "codigo": "error_actualizacion",
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Estado del contenido {id_contenido} actualizado a '{nuevo_estado}'.",
                "id_contenido": id_contenido,
                "estado": nuevo_estado,
            }
        ),
        200,
    )


@api_v1_bp.get("/admin/actividades")
@admin_required
def api_admin_actividades():
    """Retorna todas las actividades y simulaciones con métricas de resolución."""
    actividades = AdminService.listar_actividades_admin()
    return jsonify({"exito": True, "total": len(actividades), "actividades": actividades}), 200


@api_v1_bp.patch("/admin/actividades/<int:id_actividad>/estado")
@admin_required
def api_admin_cambiar_estado_actividad(id_actividad: int):
    """Modifica el estado de publicación de una actividad o simulación."""
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe especificar el campo 'estado' ('publicado', 'borrador', 'desactivado').",
                    "codigo": "estado_requerido",
                }
            ),
            400,
        )

    exito, error_msg = AdminService.actualizar_estado_actividad(
        id_actividad=id_actividad, nuevo_estado=str(nuevo_estado)
    )
    if not exito:
        status_code = 404 if "no existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al actualizar estado de la actividad.",
                    "codigo": "error_actualizacion",
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Estado de la actividad {id_actividad} actualizado a '{nuevo_estado}'.",
                "id_actividad": id_actividad,
                "estado": nuevo_estado,
            }
        ),
        200,
    )


@api_v1_bp.get("/admin/evaluaciones")
@admin_required
def api_admin_evaluaciones():
    """Retorna todas las evaluaciones con sus indicadores de rendimiento."""
    evaluaciones = AdminService.listar_evaluaciones_admin()
    return jsonify({"exito": True, "total": len(evaluaciones), "evaluaciones": evaluaciones}), 200


@api_v1_bp.patch("/admin/evaluaciones/<int:id_evaluacion>/estado")
@admin_required
def api_admin_cambiar_estado_evaluacion(id_evaluacion: int):
    """Modifica el estado de publicación de una evaluación formal."""
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if not nuevo_estado:
        return (
            jsonify(
                {
                    "exito": False,
                    "error": "Debe especificar el campo 'estado' ('publicado', 'borrador', 'desactivado').",
                    "codigo": "estado_requerido",
                }
            ),
            400,
        )

    exito, error_msg = AdminService.actualizar_estado_evaluacion(
        id_evaluacion=id_evaluacion, nuevo_estado=str(nuevo_estado)
    )
    if not exito:
        status_code = 404 if "no existe" in (error_msg or "").lower() else 400
        return (
            jsonify(
                {
                    "exito": False,
                    "error": error_msg or "Error al actualizar estado de la evaluación.",
                    "codigo": "error_actualizacion",
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": f"Estado de la evaluación {id_evaluacion} actualizado a '{nuevo_estado}'.",
                "id_evaluacion": id_evaluacion,
                "estado": nuevo_estado,
            }
        ),
        200,
    )
