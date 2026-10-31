"""Capa de compatibilidad hacia atrás para importaciones desde app.models.entities.

Los modelos han sido particionados modularmente por dominio en:
- app.models.base
- app.models.auth
- app.models.aprendizaje
- app.models.actividades
- app.models.evaluacion
- app.models.progreso
"""

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
