"""Modelos de autenticación, roles y usuarios en MDG Cibersegura."""

from datetime import datetime
from typing import TYPE_CHECKING

from flask_login import UserMixin
from sqlalchemy import DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import utc_now

if TYPE_CHECKING:
    from app.models.actividades import IntentoActividad
    from app.models.evaluacion import IntentoEvaluacion
    from app.models.progreso import ProgresoContenido


class Rol(db.Model):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id_rol"), nullable=False)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activo", nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    rol: Mapped[Rol] = relationship(back_populates="usuarios")
    progresos: Mapped[list["ProgresoContenido"]] = relationship(back_populates="usuario")
    intentos_actividad: Mapped[list["IntentoActividad"]] = relationship(back_populates="usuario")
    intentos_evaluacion: Mapped[list["IntentoEvaluacion"]] = relationship(back_populates="usuario")

    def get_id(self) -> str:
        return str(self.id_usuario)

    @property
    def is_active(self) -> bool:
        return self.estado == "activo"

    @property
    def es_administrador(self) -> bool:
        return self.rol is not None and self.rol.nombre == "administrador"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def normalizar_correo(correo: str) -> str:
        return correo.strip().lower()

    @classmethod
    def buscar_por_correo(cls, correo: str) -> "Usuario | None":
        correo_normalizado = cls.normalizar_correo(correo)
        return db.session.scalar(select(cls).where(cls.correo == correo_normalizado))

    @classmethod
    def registrar_ciudadano(
        cls,
        nombres: str,
        apellidos: str,
        correo: str,
        password: str,
    ) -> "Usuario":
        rol_ciudadano = db.session.scalar(select(Rol).where(Rol.nombre == "ciudadano"))
        if rol_ciudadano is None:
            raise RuntimeError("No se encontró el rol de ciudadano.")

        usuario = cls(
            id_rol=rol_ciudadano.id_rol,
            nombres=nombres.strip(),
            apellidos=apellidos.strip(),
            correo=cls.normalizar_correo(correo),
            estado="activo",
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        return usuario

    @classmethod
    def autenticar(cls, correo: str, password: str) -> "Usuario | None":
        usuario = cls.buscar_por_correo(correo)
        if usuario is None or not usuario.check_password(password):
            return None
        return usuario

    def obtener_resumen_progreso(self) -> dict:
        from app.core.progreso_service import ProgresoService

        return ProgresoService.obtener_resumen_progreso_usuario(self.id_usuario)
