from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Rol(db.Model):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(db.Model):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id_rol"), nullable=False)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activo", nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    rol: Mapped[Rol] = relationship(back_populates="usuarios")
    progresos: Mapped[list["ProgresoContenido"]] = relationship(back_populates="usuario")
    intentos_actividad: Mapped[list["IntentoActividad"]] = relationship(back_populates="usuario")
    intentos_evaluacion: Mapped[list["IntentoEvaluacion"]] = relationship(back_populates="usuario")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


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


class Actividad(db.Model):
    __tablename__ = "actividad"

    id_actividad: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_tema: Mapped[int] = mapped_column(ForeignKey("tema.id_tema"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    instrucciones: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="publicado", nullable=False)

    tema: Mapped[Tema] = relationship(back_populates="actividades")
    intentos: Mapped[list["IntentoActividad"]] = relationship(back_populates="actividad")


class Evaluacion(db.Model):
    __tablename__ = "evaluacion"

    id_evaluacion: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_tema: Mapped[int] = mapped_column(ForeignKey("tema.id_tema"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    puntaje_minimo: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="publicado", nullable=False)

    tema: Mapped[Tema] = relationship(back_populates="evaluaciones")
    preguntas: Mapped[list["Pregunta"]] = relationship(back_populates="evaluacion")
    intentos: Mapped[list["IntentoEvaluacion"]] = relationship(back_populates="evaluacion")


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

    usuario: Mapped[Usuario] = relationship(back_populates="progresos")
    contenido: Mapped[Contenido] = relationship(back_populates="progresos")


class IntentoActividad(db.Model):
    __tablename__ = "intento_actividad"

    id_intento_actividad: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_actividad: Mapped[int] = mapped_column(ForeignKey("actividad.id_actividad"), nullable=False)
    resultado: Mapped[str | None] = mapped_column(String(100))
    fecha_intento: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    usuario: Mapped[Usuario] = relationship(back_populates="intentos_actividad")
    actividad: Mapped[Actividad] = relationship(back_populates="intentos")


class IntentoEvaluacion(db.Model):
    __tablename__ = "intento_evaluacion"

    id_intento_evaluacion: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"), nullable=False)
    id_evaluacion: Mapped[int] = mapped_column(ForeignKey("evaluacion.id_evaluacion"), nullable=False)
    puntaje_obtenido: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fecha_intento: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    usuario: Mapped[Usuario] = relationship(back_populates="intentos_evaluacion")
    evaluacion: Mapped[Evaluacion] = relationship(back_populates="intentos")
    respuestas: Mapped[list["Respuesta"]] = relationship(back_populates="intento")


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
