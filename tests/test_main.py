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


# ---------------------------------------------------------------------------
# Rediseño de la portada: datos dinámicos, estados y accesibilidad estructural
# ---------------------------------------------------------------------------
import re  # noqa: E402

from app.models.entities import IntentoActividad, ProgresoContenido  # noqa: E402
from app.models.evaluacion import IntentoEvaluacion  # noqa: E402


def _usuario_ciudadano():
    return db.session.scalar(db.select(Usuario).where(Usuario.correo == "ciudadano@ejemplo.com"))


def _tema(orden):
    return db.session.scalar(db.select(Tema).where(Tema.orden == orden))


def test_portada_no_usa_imagenes_rasterizadas_ni_emojis(client):
    """La identidad gráfica es CSS/SVG propia: sin <img>, sin hero.jpg y sin emojis."""
    html_anonimo = client.get("/").get_data(as_text=True)
    login_ciudadano(client)
    html_ciudadano = client.get("/").get_data(as_text=True)

    for html in (html_anonimo, html_ciudadano):
        assert "<img" not in html
        assert "hero.jpg" not in html
        assert not re.search(r"tema-\d+\.jpg", html)
        assert not re.search("[\U0001F300-\U0001FAFF\u2600-\u27BF]", html)
        assert html.count("<h1") == 1
        assert 'class="modulos-grid"' in html
        assert 'aria-hidden="true"' in html


def test_visitante_ve_cifras_reales_del_catalogo(client):
    """Las cifras de la lámina salen de los datos publicados, no son valores fijos."""
    html = client.get("/").get_data(as_text=True)
    n_temas = db.session.scalar(
        db.select(db.func.count()).select_from(Tema).where(Tema.estado == "publicado")
    )
    n_lecciones = db.session.scalar(
        db.select(db.func.count()).select_from(Contenido).where(Contenido.estado == "publicado")
    )

    assert "Programa formativo" in html
    assert re.search(r"Módulos</dt>\s*<dd[^>]*>%d</dd>" % n_temas, html)
    assert re.search(r"Lecciones</dt>\s*<dd[^>]*>%d</dd>" % n_lecciones, html)
    assert html.count('<article class="modulo ') == n_temas
    # El visitante no ve progreso personal ni la barra de avance
    assert 'role="progressbar"' not in html
    assert "Tu avance general" not in html
    assert "Crear una cuenta" in html


def test_ciudadano_sin_avance_muestra_estado_inicial(client):
    login_ciudadano(client)
    html = client.get("/").get_data(as_text=True)

    assert 'role="progressbar"' in html
    assert "Sin iniciar" in html
    assert "Tu siguiente paso" in html
    assert "Lecciones</dt>" in html
    assert re.search(r"0 de \d+ módulos completados", html)
    # Ningún módulo se presenta como completado ni «en curso» sin avance real
    assert "Módulo completado" not in html
    assert "En curso" not in html


def test_ciudadano_con_avance_refleja_datos_reales(client):
    login_ciudadano(client)
    usuario = _usuario_ciudadano()
    tema1 = _tema(1)
    for contenido in tema1.contenidos:
        ProgresoContenido.marcar_completado(usuario.id_usuario, contenido.id_contenido, True)
    n = len(tema1.contenidos)

    html = client.get("/").get_data(as_text=True)
    assert "%d de %d lecciones" % (n, n) in html
    assert "100%" in html
    # Con lecciones completas y práctica pendiente, el siguiente paso es el taller
    assert "Realizar taller práctico" in html
    assert "Práctica pendiente" in html


def test_estados_completado_y_evaluacion_por_repasar(client):
    login_ciudadano(client)
    usuario = _usuario_ciudadano()
    for orden, puntaje in ((1, 20), (2, 1)):
        tema = _tema(orden)
        for contenido in tema.contenidos:
            ProgresoContenido.marcar_completado(usuario.id_usuario, contenido.id_contenido, True)
        for actividad in tema.actividades:
            IntentoActividad.registrar(usuario.id_usuario, actividad.id_actividad, "exitoso")
        for evaluacion in tema.evaluaciones:
            db.session.add(
                IntentoEvaluacion(
                    id_usuario=usuario.id_usuario,
                    id_evaluacion=evaluacion.id_evaluacion,
                    puntaje_obtenido=puntaje,
                )
            )
    db.session.commit()

    html = client.get("/").get_data(as_text=True)
    assert "Módulo completado" in html
    assert "Evaluación por repasar" in html
    assert "1 de " in html and "módulos completados" in html
    assert "modulo-completado" in html
    # El siguiente paso pasa a ser rendir de nuevo la evaluación del tema 2
    assert "Rendir evaluación" in html


def test_barras_de_progreso_tienen_semantica_accesible(client):
    login_ciudadano(client)
    html = client.get("/").get_data(as_text=True)
    barras = re.findall(r'<div class="barra-progreso-contenedor"([^>]*)>', html)
    assert barras
    for atributos in barras:
        assert 'role="progressbar"' in atributos
        for attr in ("aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-label"):
            assert attr in atributos


def test_cada_modulo_tiene_un_unico_enlace_con_nombre_visible(client):
    html = client.get("/").get_data(as_text=True)
    articulos = re.findall(r'<article class="modulo .*?</article>', html, re.S)
    assert articulos
    for art in articulos:
        enlaces = re.findall(r"<a [^>]*>(.*?)</a>", art, re.S)
        assert len(enlaces) == 1
        assert enlaces[0].strip()
