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
        intentos_exitosos = set(
            db.session.scalars(
                select(IntentoActividad.id_actividad).where(
                    IntentoActividad.id_usuario == id_usuario,
                    IntentoActividad.resultado == "exitoso",
                )
            ).all()
        )

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
                estado = "no_iniciado"
            elif completadas_tema == total_tema:
                estado = "completado"
            else:
                estado = "en_progreso"

            siguiente = next(
                (c for c in lecciones_publicadas if c.id_contenido not in completados),
                None,
            )

            # Actividades del tema
            actividades_publicadas = [a for a in tema.actividades if a.estado == "publicado"]
            tot_act = len(actividades_publicadas)
            comp_act = sum(1 for a in actividades_publicadas if a.id_actividad in intentos_exitosos)
            total_actividades_global += tot_act
            total_actividades_completadas_global += comp_act

            # Evaluación del tema
            evaluacion_pub = next((e for e in tema.evaluaciones if e.estado == "publicado"), None)
            eval_info = None
            if evaluacion_pub:
                total_evaluaciones_global += 1
                mejor_intento = evaluacion_pub.obtener_mejor_intento(id_usuario)
                aprobado = mejor_intento is not None and mejor_intento.puntaje_obtenido >= evaluacion_pub.puntaje_minimo
                if aprobado:
                    evaluaciones_aprobadas_global += 1
                eval_info = {
                    "evaluacion": evaluacion_pub,
                    "mejor_intento": mejor_intento,
                    "aprobado": aprobado,
                }

            temas_resumen.append(
                {
                    "tema": tema,
                    "total_lecciones": total_tema,
                    "lecciones_completadas": completadas_tema,
                    "total_actividades": tot_act,
                    "actividades_completadas": comp_act,
                    "evaluacion_info": eval_info,
                    "porcentaje": porcentaje,
                    "estado": estado,
                    "siguiente_leccion": siguiente,
                }
            )

        porcentaje_global = (
            round((total_completadas_global / total_lecciones_global) * 100)
            if total_lecciones_global > 0
            else 0
        )
        temas_completados = sum(1 for t in temas_resumen if t["estado"] == "completado")

        return {
            "total_lecciones": total_lecciones_global,
            "lecciones_completadas": total_completadas_global,
            "total_actividades": total_actividades_global,
            "actividades_completadas": total_actividades_completadas_global,
            "total_evaluaciones": total_evaluaciones_global,
            "evaluaciones_aprobadas": evaluaciones_aprobadas_global,
            "porcentaje_global": porcentaje_global,
            "total_temas": len(temas),
            "temas_completados": temas_completados,
            "temas": temas_resumen,
        }
