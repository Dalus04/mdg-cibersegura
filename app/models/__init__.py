"""Modelos de datos del sistema MDG Cibersegura particionados por dominio."""

from app.models.actividades import Actividad, IntentoActividad
from app.models.aprendizaje import Contenido, Tema
from app.models.auth import Rol, Usuario
from app.models.base import utc_now
from app.models.evaluacion import (
    Alternativa,
    Evaluacion,
    IntentoEvaluacion,
    Pregunta,
    Respuesta,
)
from app.models.progreso import ProgresoContenido

__all__ = [
    "Actividad",
    "Alternativa",
    "Contenido",
    "Evaluacion",
    "IntentoActividad",
    "IntentoEvaluacion",
    "Pregunta",
    "ProgresoContenido",
    "Respuesta",
    "Rol",
    "Tema",
    "Usuario",
    "utc_now",
]
