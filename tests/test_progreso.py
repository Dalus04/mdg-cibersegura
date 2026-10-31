from app.extensions import db
from app.models import Contenido, ProgresoContenido, Tema, Usuario


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


def test_mi_progreso_requiere_autenticacion(client):
    response = client.get("/mi-progreso")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_marcar_completado_requiere_autenticacion(client):
    response = client.post("/temas/1/contenidos/1/completar")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_desmarcar_completado_requiere_autenticacion(client):
    response = client.post("/temas/1/contenidos/1/desmarcar")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_mi_progreso_estado_inicial_sin_lecciones(client):
    login_ciudadano(client)
    response = client.get("/mi-progreso")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Mi progreso de aprendizaje" in html
    assert "0%" in html
    assert "No iniciado" in html
    assert "Gestión de contraseñas seguras y autenticación" in html


def test_marcar_leccion_completada_exitoso(client, app):
    login_ciudadano(client)

    # Marcar lección 1 del tema 1
    response = client.post(
        "/temas/1/contenidos/1/completar",
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "¡Excelente avance! Marcaste" in html
    assert "Has completado esta lección formativa" in html
    assert "Marcar como pendiente" in html

    # Verificar en la base de datos
    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        progreso = db.session.scalar(
            db.select(ProgresoContenido).where(
                ProgresoContenido.id_usuario == usuario.id_usuario,
                ProgresoContenido.id_contenido == 1,
            )
        )
        assert progreso is not None
        assert progreso.completado is True
        assert progreso.fecha_completado is not None


def test_detalle_tema_muestra_leccion_completada(client):
    login_ciudadano(client)
    client.post("/temas/1/contenidos/1/completar", follow_redirects=True)

    response = client.get("/temas/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Completada" in html
    assert "Tu avance" in html
    assert "1 de" in html


def test_catalogo_temas_muestra_progreso_usuario(client):
    login_ciudadano(client)
    client.post("/temas/1/contenidos/1/completar", follow_redirects=True)

    response = client.get("/temas")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Avance: 1/" in html


def test_desmarcar_leccion_completada(client, app):
    login_ciudadano(client)

    # Marcar
    client.post("/temas/1/contenidos/1/completar", follow_redirects=True)
    # Desmarcar
    response = client.post(
        "/temas/1/contenidos/1/desmarcar",
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Se actualizó la lección" in html
    assert "pendiente de estudio" in html
    assert "Marcar lección como completada" in html

    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        progreso = db.session.scalar(
            db.select(ProgresoContenido).where(
                ProgresoContenido.id_usuario == usuario.id_usuario,
                ProgresoContenido.id_contenido == 1,
            )
        )
        assert progreso is not None
        assert progreso.completado is False
        assert progreso.fecha_completado is None


def test_marcar_leccion_inexistente_retorna_404(client):
    login_ciudadano(client)
    response = client.post("/temas/1/contenidos/9999/completar")
    assert response.status_code == 404


def test_marcar_leccion_tema_inexistente_retorna_404(client):
    login_ciudadano(client)
    response = client.post("/temas/9999/contenidos/1/completar")
    assert response.status_code == 404


def test_resumen_progreso_usuario_calcula_metricas(app):
    with app.app_context():
        usuario = Usuario.buscar_por_correo("ciudadano@ejemplo.com")
        tema1 = db.session.scalar(db.select(Tema).where(Tema.id_tema == 1))
        lecciones_tema1 = [c for c in tema1.contenidos if c.estado == "publicado"]

        # Marcar todas las lecciones del tema 1
        for leccion in lecciones_tema1:
            ProgresoContenido.marcar_completado(usuario.id_usuario, leccion.id_contenido, True)

        resumen = ProgresoContenido.obtener_resumen_progreso_usuario(usuario.id_usuario)

        assert resumen["total_lecciones"] >= len(lecciones_tema1)
        assert resumen["lecciones_completadas"] == len(lecciones_tema1)
        assert resumen["temas_completados"] >= 1

        tema1_resumen = next(t for t in resumen["temas"] if t["tema"].id_tema == 1)
        assert tema1_resumen["porcentaje"] == 100
        assert tema1_resumen["estado"] == "completado"
        assert tema1_resumen["siguiente_leccion"] is None
