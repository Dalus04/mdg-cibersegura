"""Servicio de gestión del catálogo de temas, lecciones y lectura formativa en MDG Cibersegura."""

import re
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.entities import (
    Actividad,
    Contenido,
    Evaluacion,
    IntentoActividad,
    Pregunta,
    ProgresoContenido,
    Tema,
)


class AprendizajeService:
    """Orquesta la navegación temática, la lectura formativa y el seguimiento lección por lección."""

    @classmethod
    def parsear_bloques_contenido(cls, texto_contenido: str) -> list[dict[str, Any]]:
        """Convierte el texto en bloques semánticos (párrafos, subtítulos, listas ordenadas y desordenadas)."""
        parrafos_crudos = [p.strip() for p in texto_contenido.split("\n\n") if p.strip()]
        bloques: list[dict[str, Any]] = []

        for parrafo in parrafos_crudos:
            lineas = [line.strip() for line in parrafo.split("\n") if line.strip()]
            if not lineas:
                continue

            es_lista_bullets = all(l.startswith(("•", "-", "*")) for l in lineas)
            es_lista_numeros = all(
                l and l[0].isdigit() and ("." in l[:4] or ")" in l[:4]) for l in lineas
            )

            if es_lista_bullets:
                items = [re.sub(r"^[•\-*]\s*", "", l) for l in lineas]
                bloques.append({"tipo": "lista_desordenada", "elementos": items})
                continue

            if es_lista_numeros:
                items = [re.sub(r"^\d+[\.\)]\s*", "", l) for l in lineas]
                bloques.append({"tipo": "lista_ordenada", "elementos": items})
                continue

            if len(lineas) > 1:
                primera_linea = lineas[0]
                lineas_restantes = lineas[1:]
                resto_es_bullets = all(
                    l.startswith(("•", "-", "*")) for l in lineas_restantes
                )
                resto_es_numeros = all(
                    l and l[0].isdigit() and ("." in l[:4] or ")" in l[:4])
                    for l in lineas_restantes
                )

                if resto_es_bullets or resto_es_numeros:
                    if primera_linea.endswith(":"):
                        bloques.append(
                            {"tipo": "subtitulo", "texto": primera_linea.rstrip(":")}
                        )
                    else:
                        bloques.append({"tipo": "parrafo", "texto": primera_linea})

                    if resto_es_bullets:
                        items = [re.sub(r"^[•\-*]\s*", "", l) for l in lineas_restantes]
                        bloques.append({"tipo": "lista_desordenada", "elementos": items})
                    else:
                        items = [re.sub(r"^\d+[\.\)]\s*", "", l) for l in lineas_restantes]
                        bloques.append({"tipo": "lista_ordenada", "elementos": items})
                    continue

            bloques.append({"tipo": "parrafo", "texto": parrafo})

        return bloques

    @classmethod
    def obtener_catalogo_temas(
        cls, id_usuario: int | None = None
    ) -> tuple[list[Tema], dict[int, dict[str, Any]]]:
        """Devuelve los temas publicados y el mapa de progreso por id_tema si el usuario está autenticado."""
        temas = db.session.scalars(
            select(Tema)
            .where(Tema.estado == "publicado")
            .order_by(Tema.orden)
            .options(
                selectinload(Tema.contenidos),
                selectinload(Tema.actividades),
            )
        ).all()

        progreso_por_tema: dict[int, dict[str, Any]] = {}
        if id_usuario is not None:
            completados = ProgresoContenido.obtener_completados_usuario(id_usuario)
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

        return temas, progreso_por_tema

    @classmethod
    def obtener_detalle_tema(
        cls, id_tema: int, id_usuario: int | None = None
    ) -> dict[str, Any] | None:
        """Obtiene la información integral de un tema (lecciones, actividades, evaluaciones e historial del usuario)."""
        tema = db.session.scalar(
            select(Tema)
            .where(Tema.id_tema == id_tema, Tema.estado == "publicado")
            .options(selectinload(Tema.contenidos))
        )
        if tema is None:
            return None

        contenidos = [c for c in tema.contenidos if c.estado == "publicado"]
        contenidos.sort(key=lambda c: c.orden)

        completados_ids: set[int] = set()
        progreso_tema = None
        if id_usuario is not None:
            ids_contenido = [c.id_contenido for c in contenidos]
            completados_ids = ProgresoContenido.obtener_completados_usuario(
                id_usuario, ids_contenido
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

        actividades = db.session.scalars(
            select(Actividad)
            .where(Actividad.id_tema == tema.id_tema, Actividad.estado == "publicado")
            .options(selectinload(Actividad.tema))
        ).all()

        intentos_actividades = {}
        if id_usuario is not None and actividades:
            for act in actividades:
                intentos_actividades[act.id_actividad] = act.obtener_ultimo_intento(id_usuario)

        evaluacion = db.session.scalar(
            select(Evaluacion)
            .where(Evaluacion.id_tema == tema.id_tema, Evaluacion.estado == "publicado")
            .options(
                selectinload(Evaluacion.preguntas).selectinload(Pregunta.alternativas)
            )
        )

        mejor_intento_eval = None
        ultimo_intento_eval = None
        if id_usuario is not None and evaluacion is not None:
            mejor_intento_eval = evaluacion.obtener_mejor_intento(id_usuario)
            ultimo_intento_eval = evaluacion.obtener_ultimo_intento(id_usuario)

        return {
            "tema": tema,
            "contenidos": contenidos,
            "completados_ids": completados_ids,
            "progreso_tema": progreso_tema,
            "actividades": actividades,
            "intentos_actividades": intentos_actividades,
            "evaluacion": evaluacion,
            "mejor_intento_eval": mejor_intento_eval,
            "ultimo_intento_eval": ultimo_intento_eval,
        }

    @classmethod
    def obtener_contenido_lectura(
        cls, id_tema: int, id_contenido: int, id_usuario: int | None = None
    ) -> dict[str, Any] | None:
        """Obtiene la lección formativa con navegación secuencial y estado de lectura del ciudadano."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return None

        contenido = db.session.scalar(
            select(Contenido).where(
                Contenido.id_contenido == id_contenido,
                Contenido.id_tema == tema.id_tema,
                Contenido.estado == "publicado",
            )
        )
        if contenido is None:
            return None

        parrafos = [p.strip() for p in contenido.contenido.split("\n\n") if p.strip()]
        bloques = cls.parsear_bloques_contenido(contenido.contenido)

        total_palabras = len(contenido.contenido.split())
        minutos_lectura = max(1, round(total_palabras / 180))

        lecciones = db.session.scalars(
            select(Contenido)
            .where(Contenido.id_tema == tema.id_tema, Contenido.estado == "publicado")
            .order_by(Contenido.orden)
        ).all()

        ids_lecciones = [c.id_contenido for c in lecciones]
        try:
            indice_actual = ids_lecciones.index(contenido.id_contenido)
        except ValueError:
            indice_actual = 0

        anterior = lecciones[indice_actual - 1] if indice_actual > 0 else None
        siguiente = (
            lecciones[indice_actual + 1]
            if indice_actual + 1 < len(lecciones)
            else None
        )

        esta_completada = False
        fecha_completado = None
        if id_usuario is not None:
            progreso = db.session.scalar(
                select(ProgresoContenido).where(
                    ProgresoContenido.id_usuario == id_usuario,
                    ProgresoContenido.id_contenido == contenido.id_contenido,
                )
            )
            if progreso and progreso.completado:
                esta_completada = True
                fecha_completado = progreso.fecha_completado

        return {
            "tema": tema,
            "contenido": contenido,
            "parrafos": parrafos,
            "bloques": bloques,
            "minutos_lectura": minutos_lectura,
            "indice": indice_actual + 1,
            "total_lecciones": len(lecciones),
            "anterior": anterior,
            "siguiente": siguiente,
            "esta_completada": esta_completada,
            "fecha_completado": fecha_completado,
        }

    @classmethod
    def actualizar_progreso_leccion(
        cls, id_tema: int, id_contenido: int, id_usuario: int, completado: bool = True
    ) -> tuple[bool, str | None]:
        """Marca o desmarca una lección como completada para el usuario autenticado."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return False, None

        contenido = db.session.scalar(
            select(Contenido).where(
                Contenido.id_contenido == id_contenido,
                Contenido.id_tema == tema.id_tema,
                Contenido.estado == "publicado",
            )
        )
        if contenido is None:
            return False, None

        ProgresoContenido.marcar_completado(
            id_usuario=id_usuario,
            id_contenido=contenido.id_contenido,
            completado=completado,
        )

        return True, contenido.titulo
