"""Modelos de actividades prácticas y simulaciones interactivas en MDG Cibersegura."""

import json
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import utc_now

if TYPE_CHECKING:
    from app.models.aprendizaje import Tema
    from app.models.auth import Usuario


class Actividad(db.Model):
    __tablename__ = "actividad"

    id_actividad: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_tema: Mapped[int] = mapped_column(ForeignKey("tema.id_tema"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    instrucciones: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="publicado", nullable=False)

    tema: Mapped["Tema"] = relationship(back_populates="actividades")
    intentos: Mapped[list["IntentoActividad"]] = relationship(back_populates="actividad")

    @property
    def configuracion(self) -> dict:
        """Parsea las instrucciones en formato JSON estructurado o devuelve dict básico."""
        if not self.instrucciones:
            return {}
        try:
            return json.loads(self.instrucciones)
        except (ValueError, TypeError):
            return {"introduccion": self.instrucciones}

    def obtener_ultimo_intento(self, id_usuario: int) -> "IntentoActividad | None":
        """Retorna el intento más reciente del usuario para esta actividad."""
        return db.session.scalar(
            select(IntentoActividad)
            .where(
                IntentoActividad.id_actividad == self.id_actividad,
                IntentoActividad.id_usuario == id_usuario,
            )
            .order_by(IntentoActividad.fecha_intento.desc())
        )


class IntentoActividad(db.Model):
    __tablename__ = "intento_actividad"

    id_intento_actividad: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_actividad: Mapped[int] = mapped_column(ForeignKey("actividad.id_actividad"), nullable=False)
    resultado: Mapped[str | None] = mapped_column(String(100))
    fecha_intento: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="intentos_actividad")
    actividad: Mapped[Actividad] = relationship(back_populates="intentos")

    @classmethod
    def registrar(
        cls, id_usuario: int, id_actividad: int, resultado: str
    ) -> "IntentoActividad":
        """Registra un nuevo intento de resolución de actividad."""
        intento = cls(
            id_usuario=id_usuario,
            id_actividad=id_actividad,
            resultado=resultado,
            fecha_intento=utc_now(),
        )
        db.session.add(intento)
        db.session.commit()
        return intento
