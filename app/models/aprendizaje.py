"""Modelos del catálogo de temas educativos y lecciones en MDG Cibersegura."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.actividades import Actividad
    from app.models.evaluacion import Evaluacion
    from app.models.progreso import ProgresoContenido


class Tema(db.Model):
    __tablename__ = "tema"

    id_tema: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="publicado", nullable=False)

    contenidos: Mapped[list["Contenido"]] = relationship(back_populates="tema")
    actividades: Mapped[list["Actividad"]] = relationship(back_populates="tema")
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="tema")


class Contenido(db.Model):
    __tablename__ = "contenido"

    id_contenido: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_tema: Mapped[int] = mapped_column(ForeignKey("tema.id_tema"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="publicado", nullable=False)

    tema: Mapped[Tema] = relationship(back_populates="contenidos")
    progresos: Mapped[list["ProgresoContenido"]] = relationship(back_populates="contenido")
