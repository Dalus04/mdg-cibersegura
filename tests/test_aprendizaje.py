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


def test_ver_contenido_renderiza_bloques_semanticos_y_tiempo_lectura(client, app):
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

    # Verifica tiempo de lectura y listas semánticas
    assert "min de lectura" in html
    assert "subtitulo-leccion" in html
    assert "lista-leccion" in html


def test_completar_leccion_con_siguiente_url_redirige_correctamente(client, app):
    from tests.test_progreso import login_ciudadano

    login_ciudadano(client)
    with app.app_context():
        tema = db.session.scalar(db.select(Tema).where(Tema.orden == 1))
        leccion1 = db.session.scalar(
            db.select(Contenido).where(Contenido.id_tema == tema.id_tema, Contenido.orden == 1)
        )
        leccion2 = db.session.scalar(
            db.select(Contenido).where(Contenido.id_tema == tema.id_tema, Contenido.orden == 2)
        )
        siguiente_url = f"/temas/{tema.id_tema}/contenidos/{leccion2.id_contenido}"

    response = client.post(
        f"/temas/{tema.id_tema}/contenidos/{leccion1.id_contenido}/completar",
        data={"siguiente_url": siguiente_url},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == siguiente_url



# ---------------------------------------------------------------------------
# Rediseño del catálogo /temas (Fase 1): tarjeta compartida, datos reales, a11y
# ---------------------------------------------------------------------------
import re  # noqa: E402

from app.models import IntentoActividad, IntentoEvaluacion, ProgresoContenido, Usuario  # noqa: E402
from tests.test_progreso import login_ciudadano  # noqa: E402


def _n_temas_publicados():
    return db.session.scalar(
        db.select(db.func.count()).select_from(Tema).where(Tema.estado == "publicado")
    )


def test_catalogo_sin_imagenes_ni_emojis_y_con_un_solo_h1(client):
    html = client.get("/temas").get_data(as_text=True)

    assert "<img" not in html
    assert not re.search(r"tema-\d+\.jpg", html)
    assert "hero.jpg" not in html
    assert not re.search("[\U0001F300-\U0001FAFF\u2600-\u27BF]", html)
    assert html.count("<h1") == 1
    assert 'class="modulos-grid"' in html
    # Las tarjetas son h3 bajo el h2 «Catálogo»; no hay h2 duplicados dentro de ellas
    assert "<h3 class=\"modulo-titulo\">" in html


def test_catalogo_una_tarjeta_por_tema_con_un_unico_enlace(client):
    html = client.get("/temas").get_data(as_text=True)
    articulos = re.findall(r'<article class="modulo .*?</article>', html, re.S)

    assert len(articulos) == _n_temas_publicados()
    for art in articulos:
        enlaces = re.findall(r"<a [^>]*>(.*?)</a>", art, re.S)
        assert len(enlaces) == 1  # una sola parada de teclado por tarjeta
        assert enlaces[0].strip()
        assert 'aria-hidden="true"' in art  # arte decorativo oculto a lectores de pantalla


def test_catalogo_visitante_ve_cifras_reales_e_invitacion(client):
    html = client.get("/temas").get_data(as_text=True)
    n_temas = _n_temas_publicados()

    # El visitante ve el conteo real de módulos en el filtro y en el contador vivo, sin duplicar el bloque de estadísticas de Inicio
    assert f"Mostrando {n_temas} de {n_temas} módulos formativos" in html
    assert 'class="catalogo-resumen-datos' not in html
    assert "Crea una cuenta" in html and "inicia sesión" in html
    assert "next=/temas" in html
    assert 'data-filtro-modalidad="practica"' in html
    assert 'data-filtro-modalidad="evaluacion"' in html
    assert 'role="progressbar"' not in html
    assert "Avance:" not in html


def test_catalogo_ciudadano_sin_avance(client):
    login_ciudadano(client)
    html = client.get("/temas").get_data(as_text=True)

    assert "Módulos completados" in html
    assert re.search(r"Lecciones leídas</dt>\s*<dd>0 <small>de \d+</small>", html)
    assert "Sin iniciar" in html
    assert "Avance: 0/" in html
    assert "Crea una cuenta" not in html
    # Un único módulo se resalta como «siguiente paso»
    assert html.count("modulo-actual") == 1
    assert "En curso" not in html
    assert "Módulo completado" not in html


def test_catalogo_refleja_estados_igual_que_la_portada(client, app):
    login_ciudadano(client)
    with app.app_context():
        usuario = db.session.scalar(db.select(Usuario).where(Usuario.correo == "ciudadano@ejemplo.com"))
        for orden, puntaje in ((1, 20), (2, 1)):
            tema = db.session.scalar(db.select(Tema).where(Tema.orden == orden))
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

    html = client.get("/temas").get_data(as_text=True)
    inicio = client.get("/").get_data(as_text=True)

    for texto in ("Módulo completado", "Evaluación por repasar"):
        assert texto in html and texto in inicio
    assert "modulo-completado" in html
    assert "Avance: 3/3 lecciones" in html
    assert re.search(r"Módulos completados</dt>\s*<dd>1 <small>de ", html)
    # El módulo resaltado es el que tiene el siguiente paso (evaluación del tema 2)
    assert html.count("modulo-actual") == 1
    assert re.search(r'modulo-t2[^"]*modulo-actual', html)


def test_catalogo_barras_de_progreso_tienen_aria_completo(client):
    login_ciudadano(client)
    html = client.get("/temas").get_data(as_text=True)
    barras = re.findall(r'<div class="barra-progreso-contenedor"([^>]*)>', html)

    assert barras
    for atributos in barras:
        assert 'role="progressbar"' in atributos
        for attr in ("aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-label"):
            assert attr in atributos


def test_catalogo_fichas_curriculares_con_temario_y_filtros_accesibles(client, app):
    """Verifica que /temas renderice fichas curriculares limpias con avance sintético y filtros en dos niveles."""
    login_ciudadano(client)
    with app.app_context():
        usuario = db.session.scalar(db.select(Usuario).where(Usuario.correo == "ciudadano@ejemplo.com"))
        tema1 = db.session.scalar(db.select(Tema).where(Tema.orden == 1))
        leccion1 = sorted(tema1.contenidos, key=lambda c: c.orden)[0]
        ProgresoContenido.marcar_completado(usuario.id_usuario, leccion1.id_contenido, True)

    html = client.get("/temas").get_data(as_text=True)

    # Fichas curriculares diferenciadas y concisas (el listado individual de lecciones se reserva a /temas/<id>)
    assert html.count("ficha-curricular") == _n_temas_publicados()
    assert "ficha-lecciones-lista" not in html
    assert "Avance: 1/3 lecciones" in html
    assert "Tema 1 · Identidad y Privacidad" in html

    # Controles de filtrado por eje (nivel 1) y por estado (nivel 2) con aria-pressed y aria-live
    assert 'data-filtro-eje="identidad"' in html
    assert 'data-filtro-eje="fraude"' in html
    assert 'data-filtro-estado="activo"' in html
    assert 'aria-pressed="true"' in html
    assert 'aria-live="polite"' in html


# ---------------------------------------------------------------------------
# Rediseño del detalle del tema /temas/<id_tema> (Fase 2)
# ---------------------------------------------------------------------------
def test_detalle_tema_fase2_emblema_svg_sin_jpg_ni_emojis(client):
    for id_tema, variante in ((1, "tema-t1"), (2, "tema-t2"), (3, "tema-t3"), (4, "tema-t4")):
        html = client.get(f"/temas/{id_tema}").get_data(as_text=True)
        assert "<img" not in html
        assert not re.search(r"tema-\d+\.jpg", html)
        assert "hero.jpg" not in html
        assert not re.search("[\U0001F300-\U0001FAFF\u26A0]", html)
        assert f'class="encabezado-tema-hero {variante}"' in html
        assert "emblema-tema-pictograma" in html
        assert f">{id_tema:02d}</span>" in html


def test_detalle_tema_fase2_avance_integrado_y_una_parada_por_leccion(client):
    login_ciudadano(client)
    client.post("/temas/1/contenidos/1/completar", follow_redirects=True)

    html = client.get("/temas/1").get_data(as_text=True)

    # El resumen de avance vive dentro del encabezado-tema-hero
    cabecera = re.search(r'<header class="encabezado-tema-hero.*?</header>', html, re.S)
    assert cabecera is not None
    assert "Tu avance:" in cabecera.group(0)
    assert "1 de 3 completadas (33%)" in cabecera.group(0)
    assert 'role="progressbar"' in cabecera.group(0)

    # Numeración tabular 01, 02, 03 y una única parada de tabulación por fila de lección
    filas = re.findall(r'<li class="item-leccion.*?</li>', html, re.S)
    assert len(filas) == 3
    for idx, fila in enumerate(filas, start=1):
        assert f">{idx:02d}</span>" in fila
        enlaces = re.findall(r"<a [^>]*>(.*?)</a>", fila, re.S)
        assert len(enlaces) == 1

    # Lección 1 completada (Repasar lección) y Lección 2 destacada como siguiente pendiente (Leer lección →)
    assert "item-leccion-completada" in filas[0]
    assert "Repasar lección" in filas[0]
    assert "item-leccion-siguiente" in filas[1]
    assert "Leer lección →" in filas[1]
    assert "item-leccion-siguiente" not in filas[2]


# ---------------------------------------------------------------------------
# Rediseño de la lectura de lección /temas/<id_tema>/contenidos/<id_contenido> (Fase 3)
# ---------------------------------------------------------------------------
def test_lectura_leccion_fase3_cabecera_editorial_sin_banner_jpg_ni_emoji_reloj(client, app):
    with app.app_context():
        tema1 = db.session.scalar(db.select(Tema).where(Tema.orden == 1))
        leccion1 = db.session.scalar(
            db.select(Contenido).where(Contenido.id_tema == tema1.id_tema, Contenido.orden == 1)
        )
        id_tema = tema1.id_tema
        id_contenido = leccion1.id_contenido

    html = client.get(f"/temas/{id_tema}/contenidos/{id_contenido}").get_data(as_text=True)

    # Sin banner repetitivo en inglés ni emoji ⏱️
    assert "contenedor-banner-leccion" not in html
    assert "<img" not in html
    assert not re.search(r"tema-\d+\.jpg", html)
    assert "⏱" not in html

    # Cabecera editorial con sello del módulo, icono SVG de reloj e invitación sobria para visitante
    assert 'class="leccion-lectura tema-t1"' in html
    assert f"Tema 1 · {tema1.titulo}" in html
    assert "icono-reloj" in html
    assert f"next=/temas/{id_tema}/contenidos/{id_contenido}" in html


def test_lectura_leccion_fase3_indicador_completada_en_cabecera(client):
    login_ciudadano(client)
    client.post("/temas/1/contenidos/1/completar", follow_redirects=True)

    html = client.get("/temas/1/contenidos/1").get_data(as_text=True)
    encabezado = re.search(r'<header class="encabezado-leccion">.*?</header>', html, re.S)

    assert encabezado is not None
    assert "✓ Lección completada" in encabezado.group(0)
    assert "Has completado esta lección formativa" in html
    assert "Marcar como pendiente" in html


