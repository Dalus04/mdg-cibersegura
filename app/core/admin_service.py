"""Servicio de gestión administrativa, reportes institucionales y KPIs en MDG Cibersegura."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.entities import (
    Actividad,
    Contenido,
    Evaluacion,
    IntentoActividad,
    IntentoEvaluacion,
    Pregunta,
    ProgresoContenido,
    Rol,
    Tema,
    Usuario,
)


class AdminService:
    """Orquesta las operaciones del módulo de administración y la consolidación de métricas generales."""

    @classmethod
    def obtener_metricas_generales(cls) -> dict[str, Any]:
        """Calcula los indicadores clave de desempeño (KPIs) formativos e institucionales de la plataforma."""
        # 1. Métricas de Usuarios
        usuarios = db.session.scalars(
            select(Usuario).options(selectinload(Usuario.rol)).order_by(Usuario.fecha_registro.desc())
        ).all()
        total_usuarios = len(usuarios)
        total_ciudadanos = sum(1 for u in usuarios if u.rol and u.rol.nombre == "ciudadano")
        total_administradores = sum(1 for u in usuarios if u.rol and u.rol.nombre == "administrador")
        usuarios_activos = sum(1 for u in usuarios if u.is_active)
        usuarios_inactivos = total_usuarios - usuarios_activos
        ultimos_usuarios = [
            {
                "id_usuario": u.id_usuario,
                "nombres": u.nombres,
                "apellidos": u.apellidos,
                "correo": u.correo,
                "rol": u.rol.nombre if u.rol else "sin_rol",
                "estado": u.estado,
                "fecha_registro": u.fecha_registro.isoformat() if u.fecha_registro else None,
            }
            for u in usuarios[:5]
        ]

        # 2. Métricas de Contenidos y Temas
        temas = db.session.scalars(
            select(Tema)
            .order_by(Tema.orden)
            .options(
                selectinload(Tema.contenidos),
                selectinload(Tema.actividades),
                selectinload(Tema.evaluaciones),
            )
        ).all()
        total_temas = len(temas)
        total_temas_publicados = sum(1 for t in temas if t.estado == "publicado")

        todos_contenidos = [c for t in temas for c in t.contenidos]
        total_lecciones = len(todos_contenidos)
        total_lecciones_publicadas = sum(1 for c in todos_contenidos if c.estado == "publicado")

        total_lecturas_completadas = (
            db.session.scalar(
                select(func.count(ProgresoContenido.id_progreso)).where(ProgresoContenido.completado.is_(True))
            )
            or 0
        )

        # 3. Métricas de Actividades y Simulaciones
        todas_actividades = [a for t in temas for a in t.actividades]
        total_actividades = len(todas_actividades)
        total_actividades_publicadas = sum(1 for a in todas_actividades if a.estado == "publicado")

        total_intentos_actividades = db.session.scalar(select(func.count(IntentoActividad.id_intento_actividad))) or 0
        intentos_actividades_exitosos = (
            db.session.scalar(
                select(func.count(IntentoActividad.id_intento_actividad)).where(
                    IntentoActividad.resultado == "exitoso"
                )
            )
            or 0
        )
        tasa_exito_actividades = (
            round((intentos_actividades_exitosos / total_intentos_actividades) * 100, 1)
            if total_intentos_actividades > 0
            else 0.0
        )

        # 4. Métricas de Evaluaciones Formativas
        todas_evaluaciones = [e for t in temas for e in t.evaluaciones]
        total_evaluaciones = len(todas_evaluaciones)
        total_evaluaciones_publicadas = sum(1 for e in todas_evaluaciones if e.estado == "publicado")

        intentos_eval = db.session.scalars(
            select(IntentoEvaluacion).options(selectinload(IntentoEvaluacion.evaluacion))
        ).all()
        total_intentos_evaluaciones = len(intentos_eval)

        intentos_aprobados = sum(1 for i in intentos_eval if i.aprobado)
        promedio_evaluaciones = (
            round(sum(i.puntaje_obtenido for i in intentos_eval) / total_intentos_evaluaciones, 2)
            if total_intentos_evaluaciones > 0
            else 0.0
        )
        tasa_aprobacion_evaluaciones = (
            round((intentos_aprobados / total_intentos_evaluaciones) * 100, 1)
            if total_intentos_evaluaciones > 0
            else 0.0
        )

        # 5. Desglose detallado por Tema
        temas_metricas = []
        for tema in temas:
            lecciones_tema = [c for c in tema.contenidos if c.estado == "publicado"]
            ids_lecciones = [c.id_contenido for c in lecciones_tema]
            lecturas_tema = (
                db.session.scalar(
                    select(func.count(ProgresoContenido.id_progreso)).where(
                        ProgresoContenido.id_contenido.in_(ids_lecciones),
                        ProgresoContenido.completado.is_(True),
                    )
                )
                if ids_lecciones
                else 0
            )

            actividades_tema = [a for a in tema.actividades if a.estado == "publicado"]
            ids_actividades = [a.id_actividad for a in actividades_tema]
            intentos_act_tema = (
                db.session.scalar(
                    select(func.count(IntentoActividad.id_intento_actividad)).where(
                        IntentoActividad.id_actividad.in_(ids_actividades)
                    )
                )
                if ids_actividades
                else 0
            )
            exitosos_act_tema = (
                db.session.scalar(
                    select(func.count(IntentoActividad.id_intento_actividad)).where(
                        IntentoActividad.id_actividad.in_(ids_actividades),
                        IntentoActividad.resultado == "exitoso",
                    )
                )
                if ids_actividades
                else 0
            )

            evaluacion_tema = next((e for e in tema.evaluaciones if e.estado == "publicado"), None)
            intentos_eval_tema = 0
            aprobados_eval_tema = 0
            promedio_eval_tema = 0.0
            if evaluacion_tema:
                intentos_de_esta_eval = [
                    i for i in intentos_eval if i.id_evaluacion == evaluacion_tema.id_evaluacion
                ]
                intentos_eval_tema = len(intentos_de_esta_eval)
                aprobados_eval_tema = sum(1 for i in intentos_de_esta_eval if i.aprobado)
                if intentos_eval_tema > 0:
                    promedio_eval_tema = round(
                        sum(i.puntaje_obtenido for i in intentos_de_esta_eval) / intentos_eval_tema, 2
                    )

            temas_metricas.append(
                {
                    "id_tema": tema.id_tema,
                    "titulo": tema.titulo,
                    "orden": tema.orden,
                    "estado": tema.estado,
                    "total_lecciones": len(tema.contenidos),
                    "lecciones_publicadas": len(lecciones_tema),
                    "total_lecturas_completadas": lecturas_tema,
                    "total_actividades": len(tema.actividades),
                    "intentos_actividades": intentos_act_tema,
                    "exitosos_actividades": exitosos_act_tema,
                    "tiene_evaluacion": evaluacion_tema is not None,
                    "intentos_evaluacion": intentos_eval_tema,
                    "aprobados_evaluacion": aprobados_eval_tema,
                    "promedio_evaluacion": promedio_eval_tema,
                }
            )

        return {
            "usuarios": {
                "total": total_usuarios,
                "ciudadanos": total_ciudadanos,
                "administradores": total_administradores,
                "activos": usuarios_activos,
                "inactivos": usuarios_inactivos,
                "ultimos_registros": ultimos_usuarios,
            },
            "contenidos": {
                "total_temas": total_temas,
                "temas_publicados": total_temas_publicados,
                "total_lecciones": total_lecciones,
                "lecciones_publicadas": total_lecciones_publicadas,
                "total_lecturas_completadas": total_lecturas_completadas,
            },
            "actividades": {
                "total_actividades": total_actividades,
                "actividades_publicadas": total_actividades_publicadas,
                "total_intentos": total_intentos_actividades,
                "intentos_exitosos": intentos_actividades_exitosos,
                "tasa_exito": tasa_exito_actividades,
            },
            "evaluaciones": {
                "total_evaluaciones": total_evaluaciones,
                "evaluaciones_publicadas": total_evaluaciones_publicadas,
                "total_intentos": total_intentos_evaluaciones,
                "intentos_aprobados": intentos_aprobados,
                "promedio_general": promedio_evaluaciones,
                "tasa_aprobacion": tasa_aprobacion_evaluaciones,
            },
            "temas": temas_metricas,
        }

    @classmethod
    def listar_usuarios(
        cls,
        busqueda: str | None = None,
        rol_filtro: str | None = None,
        estado_filtro: str | None = None,
    ) -> list[dict[str, Any]]:
        """Devuelve el listado de usuarios con filtros opcionales y resumen de su participación."""
        query = select(Usuario).options(
            selectinload(Usuario.rol),
            selectinload(Usuario.progresos),
            selectinload(Usuario.intentos_evaluacion),
        )

        if rol_filtro:
            query = query.join(Usuario.rol).where(Rol.nombre == rol_filtro)
        if estado_filtro:
            query = query.where(Usuario.estado == estado_filtro)
        if busqueda:
            termino = f"%{busqueda.strip().lower()}%"
            query = query.where(
                Usuario.correo.ilike(termino)
                | Usuario.nombres.ilike(termino)
                | Usuario.apellidos.ilike(termino)
            )

        query = query.order_by(Usuario.fecha_registro.desc())
        usuarios = db.session.scalars(query).all()

        resultado = []
        for u in usuarios:
            lecciones_comp = sum(1 for p in u.progresos if p.completado)
            evals_aprob = sum(1 for i in u.intentos_evaluacion if i.aprobado)
            resultado.append(
                {
                    "id_usuario": u.id_usuario,
                    "nombres": u.nombres,
                    "apellidos": u.apellidos,
                    "nombre_completo": u.nombre_completo,
                    "correo": u.correo,
                    "rol": u.rol.nombre if u.rol else "sin_rol",
                    "estado": u.estado,
                    "is_active": u.is_active,
                    "es_administrador": u.es_administrador,
                    "fecha_registro": u.fecha_registro.isoformat() if u.fecha_registro else None,
                    "lecciones_completadas": lecciones_comp,
                    "evaluaciones_aprobadas": evals_aprob,
                }
            )
        return resultado

    @classmethod
    def obtener_usuario_detalle(cls, id_usuario: int) -> dict[str, Any] | None:
        """Obtiene el historial detallado de un usuario para auditoría administrativa."""
        usuario = db.session.scalar(
            select(Usuario)
            .where(Usuario.id_usuario == id_usuario)
            .options(
                selectinload(Usuario.rol),
                selectinload(Usuario.progresos).selectinload(ProgresoContenido.contenido),
                selectinload(Usuario.intentos_actividad).selectinload(IntentoActividad.actividad),
                selectinload(Usuario.intentos_evaluacion).selectinload(IntentoEvaluacion.evaluacion),
            )
        )
        if usuario is None:
            return None

        return {
            "id_usuario": usuario.id_usuario,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "correo": usuario.correo,
            "rol": usuario.rol.nombre if usuario.rol else "sin_rol",
            "estado": usuario.estado,
            "fecha_registro": usuario.fecha_registro.isoformat() if usuario.fecha_registro else None,
            "progresos": [
                {
                    "id_contenido": p.id_contenido,
                    "leccion": p.contenido.titulo if p.contenido else None,
                    "completado": p.completado,
                    "fecha_completado": p.fecha_completado.isoformat() if p.fecha_completado else None,
                }
                for p in usuario.progresos
            ],
            "intentos_actividad": [
                {
                    "id_actividad": ia.id_actividad,
                    "actividad": ia.actividad.titulo if ia.actividad else None,
                    "resultado": ia.resultado,
                    "fecha_intento": ia.fecha_intento.isoformat() if ia.fecha_intento else None,
                }
                for ia in usuario.intentos_actividad
            ],
            "intentos_evaluacion": [
                {
                    "id_evaluacion": ie.id_evaluacion,
                    "evaluacion": ie.evaluacion.titulo if ie.evaluacion else None,
                    "puntaje_obtenido": ie.puntaje_obtenido,
                    "aprobado": ie.aprobado,
                    "fecha_intento": ie.fecha_intento.isoformat() if ie.fecha_intento else None,
                }
                for ie in usuario.intentos_evaluacion
            ],
        }

    @classmethod
    def actualizar_estado_usuario(
        cls, id_usuario: int, nuevo_estado: str, id_solicitante: int | None = None
    ) -> tuple[bool, str | None]:
        """Modifica el estado activo/inactivo de un usuario, impidiendo auto-bloqueo administrativo."""
        if nuevo_estado not in ("activo", "inactivo"):
            return False, "Estado inválido. Debe ser 'activo' o 'inactivo'."

        if id_solicitante is not None and id_solicitante == id_usuario and nuevo_estado == "inactivo":
            return False, "No puedes desactivar tu propia cuenta administradora."

        usuario = db.session.get(Usuario, id_usuario)
        if usuario is None:
            return False, "Usuario no encontrado."

        usuario.estado = nuevo_estado
        db.session.commit()
        return True, None

    @classmethod
    def listar_contenidos_admin(cls) -> list[dict[str, Any]]:
        """Retorna todos los temas y contenidos sin filtro de estado para la consola de gestión."""
        temas = db.session.scalars(
            select(Tema).order_by(Tema.orden).options(selectinload(Tema.contenidos))
        ).all()

        resultado = []
        for tema in temas:
            contenidos_ordenados = sorted(tema.contenidos, key=lambda c: c.orden)
            resultado.append(
                {
                    "id_tema": tema.id_tema,
                    "titulo": tema.titulo,
                    "descripcion": tema.descripcion,
                    "orden": tema.orden,
                    "estado": tema.estado,
                    "total_lecciones": len(contenidos_ordenados),
                    "contenidos": [
                        {
                            "id_contenido": c.id_contenido,
                            "id_tema": c.id_tema,
                            "titulo": c.titulo,
                            "orden": c.orden,
                            "estado": c.estado,
                        }
                        for c in contenidos_ordenados
                    ],
                }
            )
        return resultado

    @classmethod
    def actualizar_estado_tema(cls, id_tema: int, nuevo_estado: str) -> tuple[bool, str | None]:
        """Modifica el estado de publicación de un tema ('publicado', 'borrador', 'desactivado')."""
        if nuevo_estado not in ("publicado", "borrador", "desactivado"):
            return False, "Estado no válido para el tema."

        tema = db.session.get(Tema, id_tema)
        if tema is None:
            return False, "El tema solicitado no existe."

        tema.estado = nuevo_estado
        db.session.commit()
        return True, None

    @classmethod
    def actualizar_estado_contenido(cls, id_contenido: int, nuevo_estado: str) -> tuple[bool, str | None]:
        """Modifica el estado de publicación de una lección individual."""
        if nuevo_estado not in ("publicado", "borrador", "desactivado"):
            return False, "Estado no válido para el contenido."

        contenido = db.session.get(Contenido, id_contenido)
        if contenido is None:
            return False, "La lección solicitada no existe."

        contenido.estado = nuevo_estado
        db.session.commit()
        return True, None

    @classmethod
    def listar_actividades_admin(cls) -> list[dict[str, Any]]:
        """Retorna todas las actividades y simulaciones con sus estadísticas de resolución."""
        actividades = db.session.scalars(
            select(Actividad)
            .options(selectinload(Actividad.tema), selectinload(Actividad.intentos))
            .order_by(Actividad.id_actividad)
        ).all()

        resultado = []
        for act in actividades:
            total_intentos = len(act.intentos)
            exitosos = sum(1 for i in act.intentos if i.resultado == "exitoso")
            tasa = round((exitosos / total_intentos) * 100, 1) if total_intentos > 0 else 0.0
            resultado.append(
                {
                    "id_actividad": act.id_actividad,
                    "id_tema": act.id_tema,
                    "tema_titulo": act.tema.titulo if act.tema else None,
                    "titulo": act.titulo,
                    "tipo": act.tipo,
                    "estado": act.estado,
                    "total_intentos": total_intentos,
                    "intentos_exitosos": exitosos,
                    "tasa_exito": tasa,
                }
            )
        return resultado

    @classmethod
    def actualizar_estado_actividad(cls, id_actividad: int, nuevo_estado: str) -> tuple[bool, str | None]:
        """Modifica el estado de una actividad ('publicado', 'borrador', 'desactivado')."""
        if nuevo_estado not in ("publicado", "borrador", "desactivado"):
            return False, "Estado no válido para la actividad."

        actividad = db.session.get(Actividad, id_actividad)
        if actividad is None:
            return False, "La actividad solicitada no existe."

        actividad.estado = nuevo_estado
        db.session.commit()
        return True, None

    @classmethod
    def listar_evaluaciones_admin(cls) -> list[dict[str, Any]]:
        """Retorna todas las evaluaciones con conteo de preguntas, puntaje total y notas promedio."""
        evaluaciones = db.session.scalars(
            select(Evaluacion)
            .options(
                selectinload(Evaluacion.tema),
                selectinload(Evaluacion.preguntas),
                selectinload(Evaluacion.intentos),
            )
            .order_by(Evaluacion.id_evaluacion)
        ).all()

        resultado = []
        for ev in evaluaciones:
            total_intentos = len(ev.intentos)
            aprobados = sum(1 for i in ev.intentos if i.aprobado)
            promedio = (
                round(sum(i.puntaje_obtenido for i in ev.intentos) / total_intentos, 2)
                if total_intentos > 0
                else 0.0
            )
            tasa = round((aprobados / total_intentos) * 100, 1) if total_intentos > 0 else 0.0
            resultado.append(
                {
                    "id_evaluacion": ev.id_evaluacion,
                    "id_tema": ev.id_tema,
                    "tema_titulo": ev.tema.titulo if ev.tema else None,
                    "titulo": ev.titulo,
                    "puntaje_minimo": ev.puntaje_minimo,
                    "puntaje_maximo": ev.puntaje_maximo,
                    "total_preguntas": len(ev.preguntas),
                    "estado": ev.estado,
                    "total_intentos": total_intentos,
                    "aprobados": aprobados,
                    "promedio_nota": promedio,
                    "tasa_aprobacion": tasa,
                }
            )
        return resultado

    @classmethod
    def actualizar_estado_evaluacion(cls, id_evaluacion: int, nuevo_estado: str) -> tuple[bool, str | None]:
        """Modifica el estado de una evaluación ('publicado', 'borrador', 'desactivado')."""
        if nuevo_estado not in ("publicado", "borrador", "desactivado"):
            return False, "Estado no válido para la evaluación."

        evaluacion = db.session.get(Evaluacion, id_evaluacion)
        if evaluacion is None:
            return False, "La evaluación solicitada no existe."

        evaluacion.estado = nuevo_estado
        db.session.commit()
        return True, None
