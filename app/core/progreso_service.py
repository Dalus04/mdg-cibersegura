"""Servicio de seguimiento y métricas de progreso ciudadano en MDG Cibersegura."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.entities import Actividad, Contenido, IntentoActividad, ProgresoContenido, Tema


class ProgresoService:
    """Orquesta las consultas y cálculos cuantitativos de aprendizaje del ciudadano."""

    @classmethod
    def obtener_resumen_progreso_usuario(cls, id_usuario: int) -> dict:
        """Calcula las métricas consolidadas de avance formativo, lecciones, actividades y evaluaciones."""
        temas = db.session.scalars(
            select(Tema)
            .where(Tema.estado == "publicado")
            .order_by(Tema.orden)
            .options(
                selectinload(Tema.contenidos),
                selectinload(Tema.actividades),
                selectinload(Tema.evaluaciones),
            )
        ).all()

        completados = ProgresoContenido.obtener_completados_usuario(id_usuario)

        # Consultar intentos de actividades del usuario
        todos_intentos_act = db.session.scalars(
            select(IntentoActividad).where(
                IntentoActividad.id_usuario == id_usuario,
            )
        ).all()
        intentos_exitosos = {ia.id_actividad for ia in todos_intentos_act if ia.resultado == "exitoso"}
        actividades_intentadas = {ia.id_actividad for ia in todos_intentos_act}

        total_lecciones_global = 0
        total_completadas_global = 0
        total_actividades_global = 0
        total_actividades_completadas_global = 0
        total_evaluaciones_global = 0
        evaluaciones_aprobadas_global = 0
        temas_resumen = []

        for tema in temas:
            lecciones_publicadas = [
                c for c in tema.contenidos if c.estado == "publicado"
            ]
            lecciones_publicadas.sort(key=lambda c: c.orden)

            total_tema = len(lecciones_publicadas)
            completadas_tema = sum(
                1 for c in lecciones_publicadas if c.id_contenido in completados
            )
            total_lecciones_global += total_tema
            total_completadas_global += completadas_tema

            porcentaje = (
                round((completadas_tema / total_tema) * 100) if total_tema > 0 else 0
            )

            if completadas_tema == 0:
                estado_lecciones = "no_iniciado"
            elif completadas_tema == total_tema:
                estado_lecciones = "completado"
            else:
                estado_lecciones = "en_progreso"

            siguiente = next(
                (c for c in lecciones_publicadas if c.id_contenido not in completados),
                None,
            )

            # Actividades del tema
            actividades_publicadas = [a for a in tema.actividades if a.estado == "publicado"]
            tot_act = len(actividades_publicadas)
            comp_act = sum(1 for a in actividades_publicadas if a.id_actividad in intentos_exitosos)
            int_act = sum(1 for a in actividades_publicadas if a.id_actividad in actividades_intentadas)
            total_actividades_global += tot_act
            total_actividades_completadas_global += comp_act

            # Evaluación del tema
            evaluacion_pub = next((e for e in tema.evaluaciones if e.estado == "publicado"), None)
            eval_info = None
            if evaluacion_pub:
                total_evaluaciones_global += 1
                mejor_intento = evaluacion_pub.obtener_mejor_intento(id_usuario)
                ultimo_intento = evaluacion_pub.obtener_ultimo_intento(id_usuario)
                aprobado = mejor_intento is not None and mejor_intento.puntaje_obtenido >= evaluacion_pub.puntaje_minimo
                if aprobado:
                    evaluaciones_aprobadas_global += 1
                eval_info = {
                    "evaluacion": evaluacion_pub,
                    "mejor_intento": mejor_intento,
                    "ultimo_intento": ultimo_intento,
                    "aprobado": aprobado,
                }

            # Estado integral del módulo
            # Un tema se considera completado integralmente si ha leído todas las lecciones,
            # completado sus actividades y aprobado su evaluación formativa.
            tiene_eval = eval_info is not None
            eval_aprobada = eval_info["aprobado"] if tiene_eval else True
            eval_intentada = (eval_info["mejor_intento"] is not None) if tiene_eval else True
            act_completas = (comp_act >= tot_act) if tot_act > 0 else True

            if total_tema == 0 and tot_act == 0 and not tiene_eval:
                estado_modulo = "no_iniciado"
            elif completadas_tema == total_tema and act_completas and eval_aprobada:
                estado_modulo = "completado"
            elif completadas_tema == total_tema and tiene_eval and not eval_intentada:
                estado_modulo = "evaluacion_pendiente"
            elif completadas_tema == total_tema and tiene_eval and not eval_aprobada:
                estado_modulo = "evaluacion_desaprobada"
            elif completadas_tema > 0 or int_act > 0 or eval_intentada:
                estado_modulo = "en_progreso"
            else:
                estado_modulo = "no_iniciado"

            # Determinación de siguiente paso pedagógico
            siguiente_paso_tema = None
            if siguiente:
                siguiente_paso_tema = {
                    "tipo": "leccion",
                    "titulo": siguiente.titulo,
                    "id_contenido": siguiente.id_contenido,
                }
            elif tot_act > 0 and comp_act < tot_act:
                siguiente_paso_tema = {
                    "tipo": "actividad",
                    "titulo": f"Taller práctico del Tema {tema.orden}",
                }
            elif tiene_eval and not eval_aprobada:
                siguiente_paso_tema = {
                    "tipo": "evaluacion",
                    "titulo": f"Evaluación del Tema {tema.orden}",
                }

            temas_resumen.append(
                {
                    "tema": tema,
                    "total_lecciones": total_tema,
                    "lecciones_completadas": completadas_tema,
                    "total_actividades": tot_act,
                    "actividades_completadas": comp_act,
                    "actividades_intentadas": int_act,
                    "evaluacion_info": eval_info,
                    "porcentaje": porcentaje,
                    "estado": estado_lecciones,
                    "estado_lecciones": estado_lecciones,
                    "estado_modulo": estado_modulo,
                    "siguiente_leccion": siguiente,
                    "siguiente_paso": siguiente_paso_tema,
                }
            )

        # Cálculo de porcentaje global ponderado integral
        ratio_lecciones = (total_completadas_global / total_lecciones_global) if total_lecciones_global > 0 else 0
        ratio_actividades = (total_actividades_completadas_global / total_actividades_global) if total_actividades_global > 0 else 0
        ratio_evaluaciones = (evaluaciones_aprobadas_global / total_evaluaciones_global) if total_evaluaciones_global > 0 else 0

        pesos_total = 0.0
        score = 0.0
        if total_lecciones_global > 0:
            score += 0.40 * ratio_lecciones
            pesos_total += 0.40
        if total_actividades_global > 0:
            score += 0.30 * ratio_actividades
            pesos_total += 0.30
        if total_evaluaciones_global > 0:
            score += 0.30 * ratio_evaluaciones
            pesos_total += 0.30

        porcentaje_global = round((score / pesos_total) * 100) if pesos_total > 0 else 0
        porcentaje_lecciones = round(ratio_lecciones * 100)

        temas_completados = sum(1 for t in temas_resumen if t["estado"] == "completado")
        modulos_completados = sum(1 for t in temas_resumen if t["estado_modulo"] == "completado")

        return {
            "total_lecciones": total_lecciones_global,
            "lecciones_completadas": total_completadas_global,
            "total_actividades": total_actividades_global,
            "actividades_completadas": total_actividades_completadas_global,
            "total_evaluaciones": total_evaluaciones_global,
            "evaluaciones_aprobadas": evaluaciones_aprobadas_global,
            "porcentaje_global": porcentaje_global,
            "porcentaje_lecciones": porcentaje_lecciones,
            "total_temas": len(temas),
            "temas_completados": temas_completados,
            "modulos_completados": modulos_completados,
            "temas": temas_resumen,
        }
