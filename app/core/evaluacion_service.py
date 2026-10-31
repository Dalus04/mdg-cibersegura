"""Servicio de gestión y calificación formal de evaluaciones en MDG Cibersegura."""

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.entities import Alternativa, Evaluacion, IntentoEvaluacion, Pregunta, Respuesta, Tema


class EvaluacionService:
    """Orquesta la obtención, validación de integridad y calificación de cuestionarios."""

    @classmethod
    def obtener_evaluacion_tema(cls, id_tema: int, id_usuario: int | None = None) -> dict[str, Any] | None:
        """Obtiene la evaluación publicada de un tema junto con sus preguntas y el historial del usuario."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return None

        evaluacion = db.session.scalar(
            select(Evaluacion)
            .where(Evaluacion.id_tema == tema.id_tema, Evaluacion.estado == "publicado")
            .options(
                selectinload(Evaluacion.preguntas).selectinload(Pregunta.alternativas)
            )
        )
        if evaluacion is None:
            return None

        mejor_intento = None
        ultimo_intento = None
        if id_usuario is not None:
            mejor_intento = evaluacion.obtener_mejor_intento(id_usuario)
            ultimo_intento = evaluacion.obtener_ultimo_intento(id_usuario)

        return {
            "tema": tema,
            "evaluacion": evaluacion,
            "mejor_intento": mejor_intento,
            "ultimo_intento": ultimo_intento,
        }

    @classmethod
    def calificar_y_registrar_intento(
        cls, id_tema: int, id_usuario: int, form_data: dict[str, Any]
    ) -> tuple[bool, IntentoEvaluacion | None, str | None]:
        """Valida que todas las preguntas hayan sido respondidas, califica el intento y persiste las respuestas."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return False, None, "El tema solicitado no existe o no se encuentra publicado."

        evaluacion = db.session.scalar(
            select(Evaluacion)
            .where(Evaluacion.id_tema == tema.id_tema, Evaluacion.estado == "publicado")
            .options(
                selectinload(Evaluacion.preguntas).selectinload(Pregunta.alternativas)
            )
        )
        if evaluacion is None:
            return False, None, "No existe una evaluación publicada para este tema."

        respuestas_dict: dict[int, int] = {}
        faltan_preguntas = False

        for pregunta in evaluacion.preguntas:
            nombre_campo = f"pregunta_{pregunta.id_pregunta}"
            valor_alt = form_data.get(nombre_campo)
            if not valor_alt or not str(valor_alt).isdigit():
                faltan_preguntas = True
                break
            respuestas_dict[pregunta.id_pregunta] = int(valor_alt)

        if faltan_preguntas or len(respuestas_dict) != len(evaluacion.preguntas):
            return (
                False,
                None,
                "Por favor, responde todas las preguntas del cuestionario antes de enviar tu evaluación.",
            )

        try:
            intento = IntentoEvaluacion.registrar_intento(
                id_usuario=id_usuario,
                evaluacion=evaluacion,
                respuestas_dict=respuestas_dict,
            )
            return True, intento, None
        except ValueError as e:
            return False, None, f"Error de validación al procesar las respuestas: {e}"

    @classmethod
    def obtener_resultado_intento(
        cls, id_tema: int, id_intento: int, id_usuario: int
    ) -> dict[str, Any] | None:
        """Obtiene el desglose pedagógico de un intento asegurando el control de acceso del usuario."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return None

        intento = db.session.scalar(
            select(IntentoEvaluacion)
            .where(
                IntentoEvaluacion.id_intento_evaluacion == id_intento,
                IntentoEvaluacion.id_usuario == id_usuario,
            )
            .options(
                selectinload(IntentoEvaluacion.evaluacion)
                .selectinload(Evaluacion.preguntas)
                .selectinload(Pregunta.alternativas),
                selectinload(IntentoEvaluacion.respuestas).selectinload(Respuesta.alternativa),
            )
        )
        if intento is None or intento.evaluacion.id_tema != tema.id_tema:
            return None

        respuestas_por_pregunta = {r.id_pregunta: r.alternativa for r in intento.respuestas}

        return {
            "tema": tema,
            "evaluacion": intento.evaluacion,
            "intento": intento,
            "respuestas_por_pregunta": respuestas_por_pregunta,
        }
