"""Pruebas unitarias y de integración para la página de inicio y la navegación principal."""

from app.extensions import db
from app.models import Contenido, Tema, Usuario


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


def login_admin(client):
    """Auxiliar para autenticar al administrador de prueba."""
    return client.post(
        "/login",
        data={
            "correo": "admin@guadalupe.gob.pe",
            "contrasena": "Admin1234!",
        },
        follow_redirects=True,
    )


def test_inicio_usuario_anonimo_muestra_temas_dinamicos(client):
    """Verifica que la portada cargue dinámicamente los temas de la BD con enlaces accesibles."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Título y encabezados
    assert "MDG Cibersegura" in html
    assert "Módulos educativos prioritarios" in html

    # Temas de la base de datos
    assert "Gestión de contraseñas seguras y autenticación" in html
    assert "Detección de enlaces fraudulentos y phishing" in html

    # Tarjetas interactivas con etiquetas de enlace
    assert 'class="enlace-tarjeta-tema"' in html
    assert "/temas/1" in html

    # Botones para anónimos
    assert "Crear una cuenta" in html
    assert "Explorar temas educativos" in html


def test_inicio_usuario_autenticado_muestra_widget_progreso(client):
    """Verifica que un ciudadano autenticado visualice su widget de avance personal."""
    login_ciudadano(client)

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Bienvenida personalizada
    assert "¡Hola, Ciudadano!" in html
    assert "Sesión iniciada como" in html
    assert "ciudadano@ejemplo.com" in html

    # Widget de progreso ciudadano
    assert "Tu avance general" in html
    assert "0%" in html
    assert "Continuar con" in html

    # Identidad en cabecera
    assert "badge-usuario-nav" in html
    assert "avatar-iniciales" in html


def test_inicio_usuario_admin_muestra_accesos_gestion(client):
    """Verifica que un administrador autenticado visualice el acceso a la consola en hero y cabecera."""
    login_admin(client)

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "¡Hola, Administrador!" in html
    assert "Consola de administración" in html
    assert "Admin" in html
    assert "/admin" in html


def test_navegacion_marca_aria_current_correctamente(client):
    """Verifica que cada ruta asigne aria-current="page" exclusivamente al enlace correspondiente."""
    # 1. Portada / Inicio
    res_inicio = client.get("/")
    assert res_inicio.status_code == 200
    html_inicio = res_inicio.get_data(as_text=True)
    assert 'href="/" aria-current="page">Inicio</a>' in html_inicio

    # 2. Catálogo de temas
    res_temas = client.get("/temas")
    assert res_temas.status_code == 200
    html_temas = res_temas.get_data(as_text=True)
    assert 'href="/temas" aria-current="page">Temas educativos</a>' in html_temas
    assert 'href="/" aria-current="page">Inicio</a>' not in html_temas

    # 3. Login
    res_login = client.get("/login")
    assert res_login.status_code == 200
    html_login = res_login.get_data(as_text=True)
    assert 'href="/login" aria-current="page">Iniciar sesión</a>' in html_login

    # 4. Registro
    res_registro = client.get("/registro")
    assert res_registro.status_code == 200
    html_registro = res_registro.get_data(as_text=True)
    assert 'href="/registro" class="boton-nav-registro" aria-current="page">Registrarse</a>' in html_registro

    # 5. Mi progreso (autenticado)
    login_ciudadano(client)
    res_progreso = client.get("/mi-progreso")
    assert res_progreso.status_code == 200
    html_progreso = res_progreso.get_data(as_text=True)
    assert 'href="/mi-progreso" aria-current="page">Mi progreso</a>' in html_progreso


def test_boton_toggle_menu_movil_presente(client):
    """Verifica que el botón de alternancia para el menú móvil cumpla con los atributos ARIA."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert 'class="boton-toggle-menu"' in html
    assert 'aria-expanded="false"' in html
    assert 'aria-controls="menu-principal"' in html
    assert 'aria-label="Abrir menú de navegación"' in html
    assert 'id="menu-principal"' in html
