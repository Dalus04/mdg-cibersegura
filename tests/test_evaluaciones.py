from app.extensions import db
from app.models import Alternativa, Evaluacion, IntentoEvaluacion, Pregunta, Rol, Tema, Usuario


def login_ciudadano(client):
    """Auxiliar para autenticar al usuario ciudadano de prueba."""
    return client.post(
        "/login",
        data={
            "correo": "ciudadano@ejemplo.com",
            "contrasena": "Ciudadano123!",
        },
        follow_redirects=True,
    )


def test_evaluaciones_iniciales_sembradas(app):
    """Verifica que las evaluaciones iniciales estén correctamente sembradas para los temas 1, 2 y 3."""
    with app.app_context():
        evaluaciones = db.session.scalars(db.select(Evaluacion)).all()
        assert len(evaluaciones) >= 3

        for eval_obj in evaluaciones:
            assert eval_obj.estado == "publicado"
            assert eval_obj.puntaje_minimo == 14.0
            assert len(eval_obj.preguntas) == 4

            total_puntaje = sum(p.puntaje for p in eval_obj.preguntas)
            assert total_puntaje == 20.0

            for preg in eval_obj.preguntas:
                assert len(preg.alternativas) >= 3
                correctas = [alt for alt in preg.alternativas if alt.es_correcta]
                assert len(correctas) == 1, f"La pregunta {preg.id_pregunta} debe tener exactamente 1 alternativa correcta"


def test_detalle_tema_muestra_seccion_evaluacion(client):
    """Verifica que el detalle del tema incluya la tarjeta de evaluación formal con sus metadatos."""
    response = client.get("/temas/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Evaluación formal del tema" in html
    assert "Evaluación formativa: Contraseñas seguras y autenticación" in html
    assert "14 / 20 pts" in html
    assert "4 enunciados" in html
    assert "Rendir evaluación →" in html


def test_ver_evaluacion_acceso_publico(client):
    """Verifica que el cuestionario sea visible públicamente y avise si el usuario no ha iniciado sesión."""
    response = client.get("/temas/1/evaluacion")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Evaluación formativa: Contraseñas seguras y autenticación" in html
    assert "Puntaje máximo:" in html
    assert "20 puntos" in html
    assert "Nota mínima de aprobación:" in html
    assert "14 puntos" in html
    assert "Para responder la evaluación formal y registrar tu calificación:" in html
    assert "Iniciar sesión" in html


def test_enviar_evaluacion_requiere_login(client):
    """Verifica que enviar respuestas requiera autenticación previa."""
    response = client.post(
        "/temas/1/evaluacion/enviar",
        data={"pregunta_1": "1"},
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_enviar_evaluacion_incompleta_muestra_error(client, app):
    """Verifica validación cuando el usuario no contesta todas las preguntas."""
    login_ciudadano(client)

    # Obtenemos la primera pregunta de la evaluación del tema 1
    with app.app_context():
        evaluacion = db.session.scalar(
            db.select(Evaluacion).where(Evaluacion.id_tema == 1)
        )
        primera_pregunta = evaluacion.preguntas[0]
        primera_alt = primera_pregunta.alternativas[0]
        data_parcial = {f"pregunta_{primera_pregunta.id_pregunta}": str(primera_alt.id_alternativa)}

    response = client.post(
        "/temas/1/evaluacion/enviar",
        data=data_parcial,
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Por favor, responde todas las preguntas del cuestionario antes de enviar tu evaluación" in html


def test_enviar_evaluacion_todas_correctas_aprueba_con_20(client, app):
    """Verifica que responder todas las preguntas correctamente registre 20 pts y estado aprobado."""
    login_ciudadano(client)

    with app.app_context():
        evaluacion = db.session.scalar(
            db.select(Evaluacion).where(Evaluacion.id_tema == 1)
        )
        respuestas_correctas = {}
        for p in evaluacion.preguntas:
            alt_correcta = next(a for a in p.alternativas if a.es_correcta)
            respuestas_correctas[f"pregunta_{p.id_pregunta}"] = str(alt_correcta.id_alternativa)

    response = client.post(
        "/temas/1/evaluacion/enviar",
        data=respuestas_correctas,
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "¡Felicitaciones! Has aprobado el cuestionario" in html
    assert "20.0" in html
    assert "Evaluación Aprobada" in html
    assert "Revisión detallada de respuestas" in html
    assert "✓ Correcta (+5 pts)" in html

    # Verificar persistencia en base de datos
    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        intento = db.session.scalar(
            db.select(IntentoEvaluacion)
            .where(
                IntentoEvaluacion.id_usuario == usuario.id_usuario,
                IntentoEvaluacion.id_evaluacion == evaluacion.id_evaluacion,
            )
            .order_by(IntentoEvaluacion.fecha_intento.desc())
        )
        assert intento is not None
        assert intento.puntaje_obtenido == 20.0
        assert intento.aprobado is True
        assert len(intento.respuestas) == 4


def test_enviar_evaluacion_desaprueba_si_menor_a_14(client, app):
    """Verifica que si el puntaje obtenido no alcanza 14.0, se marque como no aprobado."""
    login_ciudadano(client)

    with app.app_context():
        evaluacion = db.session.scalar(
            db.select(Evaluacion).where(Evaluacion.id_tema == 2)
        )
        # Seleccionar alternativas incorrectas
        respuestas_incorrectas = {}
        for p in evaluacion.preguntas:
            alt_incorrecta = next((a for a in p.alternativas if not a.es_correcta), p.alternativas[0])
            respuestas_incorrectas[f"pregunta_{p.id_pregunta}"] = str(alt_incorrecta.id_alternativa)

    response = client.post(
        "/temas/2/evaluacion/enviar",
        data=respuestas_incorrectas,
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Evaluación No Superada" in html
    assert "Puntaje insuficiente: necesitas reforzar conceptos" in html

    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        intento = db.session.scalar(
            db.select(IntentoEvaluacion)
            .where(
                IntentoEvaluacion.id_usuario == usuario.id_usuario,
                IntentoEvaluacion.id_evaluacion == evaluacion.id_evaluacion,
            )
            .order_by(IntentoEvaluacion.fecha_intento.desc())
        )
        assert intento is not None
        assert intento.puntaje_obtenido < 14.0
        assert intento.aprobado is False


def test_resultado_evaluacion_seguridad_no_acceso_otro_usuario(client, app):
    """Verifica que un usuario no pueda ver los resultados de intentos de otro usuario."""
    # 1. Registrar intento con usuario ciudadano
    login_ciudadano(client)
    with app.app_context():
        evaluacion = db.session.scalar(db.select(Evaluacion).where(Evaluacion.id_tema == 1))
        respuestas = {}
        for p in evaluacion.preguntas:
            alt_correcta = next(a for a in p.alternativas if a.es_correcta)
            respuestas[f"pregunta_{p.id_pregunta}"] = str(alt_correcta.id_alternativa)

    response = client.post(
        "/temas/1/evaluacion/enviar",
        data=respuestas,
        follow_redirects=False,
    )
    id_intento = response.headers["Location"].split("/")[-1]

    # Cerrar sesión
    client.post("/logout", follow_redirects=True)

    # 2. Crear un segundo usuario e iniciar sesión
    with app.app_context():
        rol_ciudadano = db.session.scalar(db.select(Rol).where(Rol.nombre == "ciudadano"))
        otro_usuario = Usuario(
            nombres="María",
            apellidos="Delgado",
            correo="maria@ejemplo.com",
            id_rol=rol_ciudadano.id_rol,
            estado="activo",
        )
        otro_usuario.set_password("Maria1234!")
        db.session.add(otro_usuario)
        db.session.commit()

    client.post(
        "/login",
        data={"correo": "maria@ejemplo.com", "contrasena": "Maria1234!"},
        follow_redirects=True,
    )

    # Intentar ver el intento del primer usuario
    resp_acceso = client.get(f"/temas/1/evaluacion/resultado/{id_intento}")
    assert resp_acceso.status_code == 404


def test_evaluacion_refleja_en_detalle_tema_y_mi_progreso(client, app):
    """Verifica la visualización de la calificación en el detalle del tema y en el dashboard de progreso."""
    login_ciudadano(client)

    # Aprobar la evaluación del tema 1
    with app.app_context():
        evaluacion = db.session.scalar(db.select(Evaluacion).where(Evaluacion.id_tema == 1))
        respuestas = {}
        for p in evaluacion.preguntas:
            alt_correcta = next(a for a in p.alternativas if a.es_correcta)
            respuestas[f"pregunta_{p.id_pregunta}"] = str(alt_correcta.id_alternativa)

    client.post("/temas/1/evaluacion/enviar", data=respuestas, follow_redirects=True)

    # Verificar detalle del tema
    resp_tema = client.get("/temas/1")
    assert resp_tema.status_code == 200
    html_tema = resp_tema.get_data(as_text=True)
    assert "20.0 / 20 pts" in html_tema
    assert "✓ Aprobado" in html_tema
    assert "Ver último resultado →" in html_tema
    assert "Repetir evaluación" in html_tema

    # Verificar mi progreso
    resp_progreso = client.get("/mi-progreso")
    assert resp_progreso.status_code == 200
    html_progreso = resp_progreso.get_data(as_text=True)
    assert "Evaluaciones formales" in html_progreso
    assert "1 / 3" in html_progreso
    assert "🎓 Evaluación: 20.0 pts" in html_progreso


def test_evaluacion_tema_inexistente_retorna_404(client):
    """Verifica que solicitar la evaluación de un tema inexistente retorne 404."""
    resp_get = client.get("/temas/999/evaluacion")
    assert resp_get.status_code == 404

    login_ciudadano(client)
    resp_post = client.post("/temas/999/evaluacion/enviar", data={})
    assert resp_post.status_code == 404
