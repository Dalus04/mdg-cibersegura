"""Modelos de progreso y seguimiento formativo de lecciones en MDG Cibersegura."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import utc_now

if TYPE_CHECKING:
    from app.models.aprendizaje import Contenido
    from app.models.auth import Usuario


class ProgresoContenido(db.Model):
    __tablename__ = "progreso_contenido"
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_contenido", name="uq_progreso_usuario_contenido"),
    )

    id_progreso: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_contenido: Mapped[int] = mapped_column(ForeignKey("contenido.id_contenido"), nullable=False)
    completado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_completado: Mapped[datetime | None] = mapped_column(DateTime)

    usuario: Mapped["Usuario"] = relationship(back_populates="progresos")
    contenido: Mapped["Contenido"] = relationship(back_populates="progresos")

    @classmethod
    def marcar_completado(
        cls, id_usuario: int, id_contenido: int, completado: bool = True
    ) -> "ProgresoContenido":
        """Registra o actualiza el estado de completado de una lección para un usuario."""
        progreso = db.session.scalar(
            select(cls).where(
                cls.id_usuario == id_usuario,
                cls.id_contenido == id_contenido,
            )
        )
        ahora = utc_now()
        if progreso is None:
            progreso = cls(
                id_usuario=id_usuario,
                id_contenido=id_contenido,
                completado=completado,
                fecha_completado=ahora if completado else None,
            )
            db.session.add(progreso)
        else:
            progreso.completado = completado
            progreso.fecha_completado = ahora if completado else None

        db.session.commit()
        return progreso

    @classmethod
    def obtener_completados_usuario(
        cls, id_usuario: int, ids_contenido: list[int] | None = None
    ) -> set[int]:
        """Obtiene el conjunto de IDs de contenido completados por el usuario."""
        query = select(cls.id_contenido).where(
            cls.id_usuario == id_usuario,
            cls.completado.is_(True),
        )
        if ids_contenido is not None:
            query = query.where(cls.id_contenido.in_(ids_contenido))
        return set(db.session.scalars(query).all())

    @classmethod
    def obtener_resumen_progreso_usuario(cls, id_usuario: int) -> dict:
        """Calcula las métricas de avance formativo del usuario agrupadas por tema delegando al ProgresoService."""
        from app.core.progreso_service import ProgresoService

        return ProgresoService.obtener_resumen_progreso_usuario(id_usuario)
