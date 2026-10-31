from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
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
        return ProgresoContenido.obtener_resumen_progreso_usuario(self.id_usuario)


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
        """Calcula las métricas de avance formativo del usuario agrupadas por tema."""
        temas = db.session.scalars(
            select(Tema)
            .where(Tema.estado == "publicado")
            .options(selectinload(Tema.contenidos))
            .order_by(Tema.orden)
        ).all()

        completados = cls.obtener_completados_usuario(id_usuario)

        total_lecciones_global = 0
        total_completadas_global = 0
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

            temas_resumen.append(
                {
                    "tema": tema,
                    "total_lecciones": total_tema,
                    "lecciones_completadas": completadas_tema,
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
            "porcentaje_global": porcentaje_global,
            "total_temas": len(temas),
            "temas_completados": temas_completados,
            "temas": temas_resumen,
        }


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
