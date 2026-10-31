"""Modelos de evaluaciones formales, preguntas, alternativas e intentos en MDG Cibersegura."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import utc_now

if TYPE_CHECKING:
    from app.models.aprendizaje import Tema
    from app.models.auth import Usuario


class Evaluacion(db.Model):
    __tablename__ = "evaluacion"

    id_evaluacion: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_tema: Mapped[int] = mapped_column(ForeignKey("tema.id_tema"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    puntaje_minimo: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="publicado", nullable=False)

    tema: Mapped["Tema"] = relationship(back_populates="evaluaciones")
    preguntas: Mapped[list["Pregunta"]] = relationship(back_populates="evaluacion")
    intentos: Mapped[list["IntentoEvaluacion"]] = relationship(back_populates="evaluacion")

    @property
    def puntaje_maximo(self) -> float:
        """Calcula el puntaje total sumando los puntos de sus preguntas."""
        return sum(p.puntaje for p in self.preguntas)

    def obtener_mejor_intento(self, id_usuario: int) -> "IntentoEvaluacion | None":
        """Retorna el intento con mayor puntaje obtenido por el usuario."""
        return db.session.scalar(
            select(IntentoEvaluacion)
            .where(
                IntentoEvaluacion.id_evaluacion == self.id_evaluacion,
                IntentoEvaluacion.id_usuario == id_usuario,
            )
            .order_by(
                IntentoEvaluacion.puntaje_obtenido.desc(),
                IntentoEvaluacion.fecha_intento.desc(),
            )
        )

    def obtener_ultimo_intento(self, id_usuario: int) -> "IntentoEvaluacion | None":
        """Retorna el intento cronológicamente más reciente del usuario."""
        return db.session.scalar(
            select(IntentoEvaluacion)
            .where(
                IntentoEvaluacion.id_evaluacion == self.id_evaluacion,
                IntentoEvaluacion.id_usuario == id_usuario,
            )
            .order_by(IntentoEvaluacion.fecha_intento.desc())
        )

    def ha_aprobado(self, id_usuario: int) -> bool:
        """Determina si el usuario alcanzó o superó el puntaje mínimo en algún intento."""
        mejor = self.obtener_mejor_intento(id_usuario)
        return mejor is not None and mejor.puntaje_obtenido >= self.puntaje_minimo


class Pregunta(db.Model):
    __tablename__ = "pregunta"

    id_pregunta: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_evaluacion: Mapped[int] = mapped_column(ForeignKey("evaluacion.id_evaluacion"), nullable=False)
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    puntaje: Mapped[float] = mapped_column(Float, default=1, nullable=False)

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="preguntas")
    alternativas: Mapped[list["Alternativa"]] = relationship(back_populates="pregunta")
    respuestas: Mapped[list["Respuesta"]] = relationship(back_populates="pregunta")


class Alternativa(db.Model):
    __tablename__ = "alternativa"

    id_alternativa: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_pregunta: Mapped[int] = mapped_column(ForeignKey("pregunta.id_pregunta"), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    es_correcta: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    pregunta: Mapped[Pregunta] = relationship(back_populates="alternativas")
    respuestas: Mapped[list["Respuesta"]] = relationship(back_populates="alternativa")


class IntentoEvaluacion(db.Model):
    __tablename__ = "intento_evaluacion"

    id_intento_evaluacion: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_evaluacion: Mapped[int] = mapped_column(ForeignKey("evaluacion.id_evaluacion"), nullable=False)
    puntaje_obtenido: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fecha_intento: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="intentos_evaluacion")
    evaluacion: Mapped[Evaluacion] = relationship(back_populates="intentos")
    respuestas: Mapped[list["Respuesta"]] = relationship(back_populates="intento")

    @property
    def aprobado(self) -> bool:
        """Indica si el puntaje obtenido alcanza el mínimo aprobatorio."""
        return self.puntaje_obtenido >= self.evaluacion.puntaje_minimo

    @classmethod
    def registrar_intento(
        cls, id_usuario: int, evaluacion: Evaluacion, respuestas_dict: dict[int, int]
    ) -> "IntentoEvaluacion":
        """Registra un intento formal validando la correspondencia estricta pregunta-alternativa."""
        preguntas_map = {p.id_pregunta: p for p in evaluacion.preguntas}
        puntaje_total = 0.0
        respuestas_a_guardar = []

        for id_pregunta, id_alternativa in respuestas_dict.items():
            pregunta = preguntas_map.get(id_pregunta)
            if pregunta is None:
                raise ValueError(f"La pregunta ID {id_pregunta} no pertenece a esta evaluación.")

            alternativa = next(
                (a for a in pregunta.alternativas if a.id_alternativa == id_alternativa),
                None,
            )
            if alternativa is None:
                raise ValueError(
                    f"La alternativa ID {id_alternativa} no corresponde a la pregunta ID {id_pregunta}."
                )

            if alternativa.es_correcta:
                puntaje_total += pregunta.puntaje

            respuestas_a_guardar.append((id_pregunta, id_alternativa))

        intento = cls(
            id_usuario=id_usuario,
            id_evaluacion=evaluacion.id_evaluacion,
            puntaje_obtenido=round(puntaje_total, 2),
            fecha_intento=utc_now(),
        )
        db.session.add(intento)
        db.session.flush()

        for id_pregunta, id_alternativa in respuestas_a_guardar:
            db.session.add(
                Respuesta(
                    id_intento_evaluacion=intento.id_intento_evaluacion,
                    id_pregunta=id_pregunta,
                    id_alternativa=id_alternativa,
                )
            )

        db.session.commit()
        return intento


class Respuesta(db.Model):
    __tablename__ = "respuesta"

    id_respuesta: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_intento_evaluacion: Mapped[int] = mapped_column(
        ForeignKey("intento_evaluacion.id_intento_evaluacion"), nullable=False
    )
    id_pregunta: Mapped[int] = mapped_column(ForeignKey("pregunta.id_pregunta"), nullable=False)
    id_alternativa: Mapped[int] = mapped_column(ForeignKey("alternativa.id_alternativa"), nullable=False)

    intento: Mapped[IntentoEvaluacion] = relationship(back_populates="respuestas")
    pregunta: Mapped[Pregunta] = relationship(back_populates="respuestas")
    alternativa: Mapped[Alternativa] = relationship(back_populates="respuestas")
