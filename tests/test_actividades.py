from app.extensions import db
from app.models import Actividad, IntentoActividad, Tema, Usuario


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


def test_actividades_iniciales_sembradas(app):
    with app.app_context():
        actividades = db.session.scalars(db.select(Actividad)).all()
        assert len(actividades) >= 3

        tipos = {a.tipo for a in actividades}
        assert "practica" in tipos
        assert "simulacion" in tipos


def test_detalle_tema_muestra_seccion_actividades(client):
    response = client.get("/temas/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Actividades y simulaciones del tema" in html
    assert "Taller interactivo: Creación y validación de Passphrase" in html


def test_ver_actividad_acceso_publico(client):
    response = client.get("/temas/1/actividades/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Taller interactivo: Creación y validación de Passphrase" in html
    assert "Para participar en esta actividad y registrar tu resultado" in html


def test_ver_simulacion_phishing_muestra_widget_correo(client):
    # El tema 2 tiene la simulación de phishing
    response = client.get("/temas/2/actividades/2")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Simulador de Alerta: Detección de Mensaje de Phishing Bancario" in html
    assert "Bandeja de entrada — Simulador de Ciberseguridad" in html
    assert "alerta-seguridad@bn-verificacion-urgente.net" in html
    assert "Inspección visual del enlace" in html


def test_resolver_actividad_requiere_login(client):
    response = client.post(
        "/temas/1/actividades/1/resolver",
        data={"opcion_id": "opt_3"},
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_resolver_actividad_sin_seleccion_muestra_error(client):
    login_ciudadano(client)
    response = client.post(
        "/temas/1/actividades/1/resolver",
        data={},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Por favor, selecciona una alternativa" in response.get_data(as_text=True)


def test_resolver_actividad_decision_correcta_registra_intento_exitoso(client, app):
    login_ciudadano(client)

    # En la actividad 1, la opción opt_3 (passphrase) es la correcta
    response = client.post(
        "/temas/1/actividades/1/resolver",
        data={"opcion_id": "opt_3"},
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "¡Excelente decisión defensiva!" in html
    assert "algarrobo-guitarra-rio-playa" in html
    assert "¡Correcto!" in html
    assert "Recomendación preventiva" in html

    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        intento = db.session.scalar(
            db.select(IntentoActividad).where(
                IntentoActividad.id_usuario == usuario.id_usuario,
                IntentoActividad.id_actividad == 1,
            )
        )
        assert intento is not None
        assert intento.resultado == "exitoso"


def test_resolver_simulacion_decision_incorrecta_muestra_alerta_riesgo(client, app):
    login_ciudadano(client)

    # En la simulación 2, la opción opt_hacer_clic es peligrosa
    response = client.post(
        "/temas/2/actividades/2/resolver",
        data={"opcion_id": "opt_hacer_clic"},
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Atención: esta acción pone en riesgo tus cuentas" in html
    assert "¡PELIGRO! Habrías caído en la trampa" in html

    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        intento = db.session.scalar(
            db.select(IntentoActividad).where(
                IntentoActividad.id_usuario == usuario.id_usuario,
                IntentoActividad.id_actividad == 2,
            )
        )
        assert intento is not None
        assert intento.resultado == "requiere_repaso"


def test_tema_detalle_muestra_badge_de_actividad_realizada(client):
    login_ciudadano(client)
    # Resolver exitosamente
    client.post("/temas/1/actividades/1/resolver", data={"opcion_id": "opt_3"})

    response = client.get("/temas/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Realizado con éxito" in html
    assert "Repetir actividad" in html


def test_mi_progreso_muestra_metricas_de_actividades(client):
    login_ciudadano(client)
    client.post("/temas/1/actividades/1/resolver", data={"opcion_id": "opt_3"})

    response = client.get("/mi-progreso")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Prácticas y simulaciones" in html
    assert "1 /" in html


def test_actividad_inexistente_retorna_404(client):
    response = client.get("/temas/1/actividades/9999")
    assert response.status_code == 404
