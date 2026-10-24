from app.extensions import db
from app.models import Contenido, Tema


def test_lista_temas_muestra_catalogo(client):
    response = client.get("/temas")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Temas educativos de ciberseguridad" in html
    assert "Gestión de contraseñas seguras y autenticación" in html
    assert "Detección de enlaces fraudulentos y phishing" in html
    assert "Protección de datos personales y privacidad digital" in html
    assert "Navegación segura y redes Wi-Fi públicas" in html


def test_lista_temas_no_muestra_borradores(client, app):
    with app.app_context():
        tema_borrador = Tema(
            titulo="Tema Oculto en Borrador",
            descripcion="No debe aparecer",
            orden=99,
            estado="borrador",
        )
        db.session.add(tema_borrador)
        db.session.commit()

    response = client.get("/temas")
    assert response.status_code == 200
    assert "Tema Oculto en Borrador" not in response.get_data(as_text=True)


def test_detalle_tema_exitoso(client):
    response = client.get("/temas/1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Gestión de contraseñas seguras y autenticación" in html
    assert "Lecciones del tema" in html
    assert "¿Por qué una contraseña débil pone en riesgo tus cuentas?" in html
    assert "Autenticación en dos pasos (2FA)" in html


def test_detalle_tema_inexistente_retorna_404(client):
    response = client.get("/temas/9999")
    assert response.status_code == 404


def test_detalle_tema_no_publicado_retorna_404(client, app):
    with app.app_context():
        tema_borrador = Tema(
            titulo="Tema Privado",
            descripcion="En desarrollo",
            orden=50,
            estado="borrador",
        )
        db.session.add(tema_borrador)
        db.session.commit()
        id_borrador = tema_borrador.id_tema

    response = client.get(f"/temas/{id_borrador}")
    assert response.status_code == 404


def test_ver_contenido_exitoso_con_navegacion(client, app):
    with app.app_context():
        tema = db.session.scalar(db.select(Tema).where(Tema.orden == 1))
        leccion1 = db.session.scalar(
            db.select(Contenido).where(Contenido.id_tema == tema.id_tema, Contenido.orden == 1)
        )
        id_tema = tema.id_tema
        id_leccion1 = leccion1.id_contenido

    response = client.get(f"/temas/{id_tema}/contenidos/{id_leccion1}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Verifica título y contenido
    assert "¿Por qué una contraseña débil pone en riesgo tus cuentas?" in html
    assert "fuerza bruta" in html
    assert "Lección 1 de 3" in html

    # Verifica que tiene enlace a la siguiente lección
    assert "Siguiente →" in html
    assert "Buenas prácticas para contraseñas robustas" in html


def test_ver_contenido_ultima_leccion_muestra_fin_de_tema(client, app):
    with app.app_context():
        tema = db.session.scalar(db.select(Tema).where(Tema.orden == 1))
        leccion_final = db.session.scalar(
            db.select(Contenido).where(Contenido.id_tema == tema.id_tema, Contenido.orden == 3)
        )
        id_tema = tema.id_tema
        id_final = leccion_final.id_contenido

    response = client.get(f"/temas/{id_tema}/contenidos/{id_final}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "← Anterior" in html
    assert "¡Has completado todas las lecciones de este tema!" in html


def test_ver_contenido_inexistente_o_no_correspondiente_retorna_404(client, app):
    with app.app_context():
        tema1 = db.session.scalar(db.select(Tema).where(Tema.orden == 1))
        tema2 = db.session.scalar(db.select(Tema).where(Tema.orden == 2))
        leccion_tema1 = db.session.scalar(
            db.select(Contenido).where(Contenido.id_tema == tema1.id_tema)
        )
        id_tema2 = tema2.id_tema
        id_leccion1 = leccion_tema1.id_contenido

    # Contenido con id inexistente
    res1 = client.get(f"/temas/{tema1.id_tema}/contenidos/99999")
    assert res1.status_code == 404

    # Lección que no pertenece al tema indicado
    res2 = client.get(f"/temas/{id_tema2}/contenidos/{id_leccion1}")
    assert res2.status_code == 404


def test_navegacion_global_incluye_temas(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "/temas" in html
    assert "Temas educativos" in html
    assert "Explorar temas educativos" in html
