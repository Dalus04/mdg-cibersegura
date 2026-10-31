"""Servicio de resolución de talleres y simulaciones interactivas en MDG Cibersegura."""

from typing import Any
from sqlalchemy import select

from app.extensions import db
from app.models.entities import Actividad, IntentoActividad, Tema


class ActividadService:
    """Orquesta las actividades prácticas y escenarios de simulación controlada."""

    @classmethod
    def obtener_actividad_para_resolver(
        cls, id_tema: int, id_actividad: int, id_usuario: int | None = None
    ) -> dict[str, Any] | None:
        """Obtiene la actividad interactiva publicada y el historial de intentos del usuario."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return None

        actividad = db.session.scalar(
            select(Actividad).where(
                Actividad.id_actividad == id_actividad,
                Actividad.id_tema == tema.id_tema,
                Actividad.estado == "publicado",
            )
        )
        if actividad is None:
            return None

        ultimo_intento = None
        if id_usuario is not None:
            ultimo_intento = actividad.obtener_ultimo_intento(id_usuario)

        return {
            "tema": tema,
            "actividad": actividad,
            "configuracion": actividad.configuracion,
            "ultimo_intento": ultimo_intento,
        }

    @classmethod
    def procesar_resolucion_actividad(
        cls, id_tema: int, id_actividad: int, id_usuario: int, opcion_id: str | None
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """Evalúa la alternativa seleccionada por el usuario, determina el resultado y persiste el intento."""
        tema = db.session.scalar(
            select(Tema).where(Tema.id_tema == id_tema, Tema.estado == "publicado")
        )
        if tema is None:
            return False, None, "El tema solicitado no existe o no se encuentra publicado."

        actividad = db.session.scalar(
            select(Actividad).where(
                Actividad.id_actividad == id_actividad,
                Actividad.id_tema == tema.id_tema,
                Actividad.estado == "publicado",
            )
        )
        if actividad is None:
            return False, None, "La actividad solicitada no existe o no se encuentra disponible."

        config = actividad.configuracion
        opciones = config.get("opciones", [])
        opcion_elegida = next((o for o in opciones if o.get("id") == opcion_id), None)

        if opcion_elegida is None:
            return False, None, "Por favor, selecciona una alternativa antes de enviar tu respuesta."

        es_correcta = bool(opcion_elegida.get("es_correcta"))
        resultado_clave = "exitoso" if es_correcta else "requiere_repaso"

        intento = IntentoActividad.registrar(
            id_usuario=id_usuario,
            id_actividad=actividad.id_actividad,
            resultado=resultado_clave,
        )

        return True, {
            "tema": tema,
            "actividad": actividad,
            "configuracion": config,
            "opcion_elegida": opcion_elegida,
            "es_correcta": es_correcta,
            "intento": intento,
        }, None
