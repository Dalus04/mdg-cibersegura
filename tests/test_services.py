"""Pruebas unitarias de la Capa de Servicios (app/core)."""

import pytest
from app.core import (
    ActividadService,
    AprendizajeService,
    AuthService,
    EvaluacionService,
    ProgresoService,
)
from app.extensions import db
from app.models import Evaluacion, Usuario


def test_aprendizaje_service_catalogo_y_detalle(app):
    """Verifica que AprendizajeService obtenga temas y detalle sin requerir contexto HTTP."""
    with app.app_context():
        temas, progreso = AprendizajeService.obtener_catalogo_temas()
        assert len(temas) >= 3
        assert progreso == {}

        detalle = AprendizajeService.obtener_detalle_tema(1)
        assert detalle is not None
        assert detalle["tema"].id_tema == 1
        assert len(detalle["contenidos"]) >= 1

        detalle_invalido = AprendizajeService.obtener_detalle_tema(9999)
        assert detalle_invalido is None


def test_actividad_service_validacion_y_resolucion(app):
    """Verifica la lógica de negocio de resolución de actividades en ActividadService."""
    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")

        # Sin opción
        exito, data, err = ActividadService.procesar_resolucion_actividad(1, 1, usuario.id_usuario, None)
        assert exito is False
        assert "selecciona una alternativa" in err

        # Con opción correcta
        exito, data, err = ActividadService.procesar_resolucion_actividad(1, 1, usuario.id_usuario, "opt_3")
        assert exito is True
        assert data["es_correcta"] is True
        assert data["intento"].resultado == "exitoso"


def test_evaluacion_service_calificacion(app):
    """Verifica la orquestación de calificación y verificación de integridad de EvaluacionService."""
    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        eval_data = EvaluacionService.obtener_evaluacion_tema(1, usuario.id_usuario)
        assert eval_data is not None
        evaluacion = eval_data["evaluacion"]

        # Respuestas incompletas
        exito, intento, err = EvaluacionService.calificar_y_registrar_intento(1, usuario.id_usuario, {})
        assert exito is False
        assert "responde todas las preguntas" in err

        # Respuestas completas correctas
        form_data = {}
        for p in evaluacion.preguntas:
            alt_correcta = next(a for a in p.alternativas if a.es_correcta)
            form_data[f"pregunta_{p.id_pregunta}"] = str(alt_correcta.id_alternativa)

        exito, intento, err = EvaluacionService.calificar_y_registrar_intento(1, usuario.id_usuario, form_data)
        assert exito is True
        assert intento.puntaje_obtenido == 20.0
        assert intento.aprobado is True


def test_progreso_service_calculo(app):
    """Verifica el cálculo cuantitativo en ProgresoService."""
    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        resumen = ProgresoService.obtener_resumen_progreso_usuario(usuario.id_usuario)

        assert "total_lecciones" in resumen
        assert "porcentaje_global" in resumen
        assert "evaluaciones_aprobadas" in resumen
        assert len(resumen["temas"]) >= 3


def test_auth_service_registro_duplicado_y_autenticacion(app):
    """Verifica validaciones de credenciales y registros duplicados en AuthService."""
    with app.app_context():
        # Correo duplicado
        exito, user, err = AuthService.registrar_ciudadano(
            "Carlos", "Paredes", "ciudadano@ejemplo.com", "Password123!"
        )
        assert exito is False
        assert "Ya existe una cuenta" in err

        # Autenticación fallida
        exito, user, err = AuthService.autenticar_usuario("ciudadano@ejemplo.com", "Errada123!")
        assert exito is False
        assert "Correo o contraseña incorrectos" in err

        # Autenticación exitosa
        exito, user, err = AuthService.autenticar_usuario("ciudadano@ejemplo.com", "Ciudadano123!")
        assert exito is True
        assert user is not None
        assert user.correo == "ciudadano@ejemplo.com"
