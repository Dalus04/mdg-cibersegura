from flask_login import current_user

from app.models import Usuario


def test_registro_ciudadano_exitoso(client, app):
    response = client.post(
        "/registro",
        data={
            "nombres": "Juan Carlos",
            "apellidos": "Pérez Torres",
            "correo": "juan.perez@example.com",
            "contrasena": "Password123!",
            "confirmar_contrasena": "Password123!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Tu cuenta se creó correctamente" in response.get_data(as_text=True)

    with app.app_context():
        usuario = Usuario.buscar_por_correo("juan.perez@example.com")
        assert usuario is not None
        assert usuario.nombres == "Juan Carlos"
        assert usuario.apellidos == "Pérez Torres"
        assert usuario.rol.nombre == "ciudadano"
        assert usuario.password_hash != "Password123!"
        assert usuario.check_password("Password123!") is True


def test_registro_correo_duplicado(client):
    client.post(
        "/registro",
        data={
            "nombres": "Juan",
            "apellidos": "Pérez",
            "correo": "juan@example.com",
            "contrasena": "Password123!",
            "confirmar_contrasena": "Password123!",
        },
    )

    response = client.post(
        "/registro",
        data={
            "nombres": "Otro Juan",
            "apellidos": "Pérez",
            "correo": "  JUAN@example.com  ",
            "contrasena": "Password123!",
            "confirmar_contrasena": "Password123!",
        },
    )
    assert response.status_code == 200
    assert "Ya existe una cuenta con este correo electrónico." in response.get_data(as_text=True)


def test_registro_contrasenas_no_coinciden(client):
    response = client.post(
        "/registro",
        data={
            "nombres": "Ana",
            "apellidos": "García",
            "correo": "ana@example.com",
            "contrasena": "Password123!",
            "confirmar_contrasena": "PasswordDistinta!",
        },
    )
    assert response.status_code == 200
    assert "Las contraseñas no coinciden." in response.get_data(as_text=True)


def test_registro_contrasena_corta(client):
    response = client.post(
        "/registro",
        data={
            "nombres": "Ana",
            "apellidos": "García",
            "correo": "ana@example.com",
            "contrasena": "12345",
            "confirmar_contrasena": "12345",
        },
    )
    assert response.status_code == 200
    assert "La contraseña debe tener al menos 8 caracteres." in response.get_data(as_text=True)


def test_login_exitoso(client):
    client.post(
        "/registro",
        data={
            "nombres": "Carlos",
            "apellidos": "Gómez",
            "correo": "carlos@example.com",
            "contrasena": "ClaveSegura123",
            "confirmar_contrasena": "ClaveSegura123",
        },
    )

    response = client.post(
        "/login",
        data={
            "correo": "carlos@example.com",
            "contrasena": "ClaveSegura123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Bienvenido o bienvenida, Carlos." in html
    assert "Sesión iniciada como Carlos Gómez" in html


def test_login_credenciales_invalidas(client):
    client.post(
        "/registro",
        data={
            "nombres": "Elena",
            "apellidos": "Rojas",
            "correo": "elena@example.com",
            "contrasena": "ClaveSegura123",
            "confirmar_contrasena": "ClaveSegura123",
        },
    )

    # Contraseña incorrecta
    res1 = client.post(
        "/login",
        data={"correo": "elena@example.com", "contrasena": "ClaveErronea"},
    )
    assert res1.status_code == 200
    assert "Correo o contraseña incorrectos." in res1.get_data(as_text=True)

    # Correo inexistente
    res2 = client.post(
        "/login",
        data={"correo": "nadie@example.com", "contrasena": "ClaveSegura123"},
    )
    assert res2.status_code == 200
    assert "Correo o contraseña incorrectos." in res2.get_data(as_text=True)


def test_login_cuenta_inactiva(client, app):
    client.post(
        "/registro",
        data={
            "nombres": "Mario",
            "apellidos": "Vargas",
            "correo": "mario@example.com",
            "contrasena": "ClaveSegura123",
            "confirmar_contrasena": "ClaveSegura123",
        },
    )

    with app.app_context():
        usuario = Usuario.buscar_por_correo("mario@example.com")
        usuario.estado = "inactivo"
        from app.extensions import db

        db.session.commit()

    response = client.post(
        "/login",
        data={"correo": "mario@example.com", "contrasena": "ClaveSegura123"},
    )
    assert response.status_code == 200
    assert "Tu cuenta no está activa." in response.get_data(as_text=True)


def test_login_redireccion_next_segura(client):
    client.post(
        "/registro",
        data={
            "nombres": "Sara",
            "apellidos": "Mendoza",
            "correo": "sara@example.com",
            "contrasena": "ClaveSegura123",
            "confirmar_contrasena": "ClaveSegura123",
        },
    )

    response = client.post(
        "/login?next=/contenido/1",
        data={"correo": "sara@example.com", "contrasena": "ClaveSegura123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/contenido/1"


def test_login_redireccion_next_insegura_descarta_destino_externo(client):
    client.post(
        "/registro",
        data={
            "nombres": "Sara",
            "apellidos": "Mendoza",
            "correo": "sara2@example.com",
            "contrasena": "ClaveSegura123",
            "confirmar_contrasena": "ClaveSegura123",
        },
    )

    # Intento de Open Redirect a URL externa
    response = client.post(
        "/login?next=https://sitio-malicioso.com",
        data={"correo": "sara2@example.com", "contrasena": "ClaveSegura123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_logout_cierra_sesion(client):
    client.post(
        "/registro",
        data={
            "nombres": "Lucía",
            "apellidos": "Flores",
            "correo": "lucia@example.com",
            "contrasena": "ClaveSegura123",
            "confirmar_contrasena": "ClaveSegura123",
        },
    )
    client.post(
        "/login",
        data={"correo": "lucia@example.com", "contrasena": "ClaveSegura123"},
    )

    # Logout mediante POST
    response = client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Cerraste sesión correctamente." in html
    assert "Iniciar sesión" in html


def test_logout_requiere_login(client):
    response = client.post("/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_proteccion_csrf_bloquea_post_sin_token(client_with_csrf):
    response = client_with_csrf.post(
        "/login",
        data={"correo": "alguien@example.com", "contrasena": "12345678"},
    )
    assert response.status_code == 400
    assert "CSRF" in response.get_data(as_text=True)
