"""Pruebas automatizadas del módulo de administración web de MDG Cibersegura (Fase 5)."""

from sqlalchemy import select

from app.extensions import db
from app.models import Usuario


def _login_admin(client):
    return client.post(
        "/login",
        data={"correo": "admin@guadalupe.gob.pe", "contrasena": "Admin1234!"},
        follow_redirects=True,
    )


def _login_ciudadano(client):
    return client.post(
        "/login",
        data={"correo": "ciudadano@ejemplo.com", "contrasena": "Ciudadano123!"},
        follow_redirects=True,
    )


def test_admin_acceso_no_autenticado(client):
    """Verifica que un visitante sin sesión sea redirigido a login al intentar entrar a /admin/."""
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_admin_acceso_ciudadano_prohibido(client):
    """Verifica que un ciudadano autenticado reciba 403 Forbidden al intentar acceder a /admin/."""
    _login_ciudadano(client)
    resp = client.get("/admin/")
    assert resp.status_code == 403


def test_admin_dashboard_exitoso(client):
    """Verifica que el administrador pueda acceder al panel ejecutivo y ver sus KPIs."""
    _login_admin(client)
    resp = client.get("/admin/")
    assert resp.status_code == 200
    contenido = resp.get_data(as_text=True)
    assert "Panel de Administración" in contenido
    assert "Usuarios Registrados" in contenido
    assert "Lecturas Completadas" in contenido
    assert "Efectividad en Actividades" in contenido
    assert "Rendimiento Académico por Eje Temático" in contenido


def test_admin_usuarios_lista_y_cambio_estado(client):
    """Verifica la visualización de usuarios y el cambio de estado activo/inactivo."""
    _login_admin(client)
    resp = client.get("/admin/usuarios")
    assert resp.status_code == 200
    contenido = resp.get_data(as_text=True)
    assert "Gestión de Usuarios" in contenido
    assert "ciudadano@ejemplo.com" in contenido

    # Obtener el ID del ciudadano
    ciudadano = db.session.scalar(
        select(Usuario).where(Usuario.correo == "ciudadano@ejemplo.com")
    )
    assert ciudadano is not None

    # Desactivar ciudadano
    resp_des = client.post(
        f"/admin/usuarios/{ciudadano.id_usuario}/estado",
        data={"estado": "inactivo"},
        follow_redirects=True,
    )
    assert resp_des.status_code == 200
    db.session.refresh(ciudadano)
    html_des = resp_des.get_data(as_text=True)
    assert "actualizado a" in html_des and "inactivo" in html_des

    # Reactivar
    resp_act = client.post(
        f"/admin/usuarios/{ciudadano.id_usuario}/estado",
        data={"estado": "activo"},
        follow_redirects=True,
    )
    assert resp_act.status_code == 200
    db.session.refresh(ciudadano)
    assert ciudadano.estado == "activo"


def test_admin_usuarios_auto_desactivacion_bloqueada(client):
    """Verifica que un administrador no pueda desactivar su propia cuenta en uso."""
    _login_admin(client)
    admin_usr = db.session.scalar(
        select(Usuario).where(Usuario.correo == "admin@guadalupe.gob.pe")
    )
    assert admin_usr is not None

    resp = client.post(
        f"/admin/usuarios/{admin_usr.id_usuario}/estado",
        data={"estado": "inactivo"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(admin_usr)
    assert admin_usr.estado == "activo"
    assert "No puedes desactivar tu propia cuenta" in resp.get_data(as_text=True)


def test_admin_contenidos_y_cambio_estado(client):
    """Verifica la gestión de temas y cambio de estado de publicación."""
    _login_admin(client)
    resp = client.get("/admin/contenidos")
    assert resp.status_code == 200
    contenido = resp.get_data(as_text=True)
    assert "Gestión de Contenidos y Temas" in contenido

    # Cambiar estado de tema 1 a borrador
    resp_tema = client.post(
        "/admin/temas/1/estado",
        data={"estado": "borrador"},
        follow_redirects=True,
    )
    html_tema = resp_tema.get_data(as_text=True)
    assert "actualizado a" in html_tema and "borrador" in html_tema

    # Restaurar
    client.post("/admin/temas/1/estado", data={"estado": "publicado"}, follow_redirects=True)


def test_admin_actividades_vista_y_estado(client):
    """Verifica la vista administrativa de actividades y simulaciones."""
    _login_admin(client)
    resp = client.get("/admin/actividades")
    assert resp.status_code == 200
    contenido = resp.get_data(as_text=True)
    assert "Gestión de Actividades y Simulaciones" in contenido
    assert "Taller interactivo" in contenido or "Simulación" in contenido

    # Cambiar estado
    resp_toggle = client.post(
        "/admin/actividades/1/estado",
        data={"estado": "borrador"},
        follow_redirects=True,
    )
    assert resp_toggle.status_code == 200

    # Restaurar
    client.post("/admin/actividades/1/estado", data={"estado": "publicado"}, follow_redirects=True)


def test_admin_evaluaciones_vista_y_estado(client):
    """Verifica la supervisión de evaluaciones formales."""
    _login_admin(client)
    resp = client.get("/admin/evaluaciones")
    assert resp.status_code == 200
    contenido = resp.get_data(as_text=True)
    assert "Gestión de Evaluaciones Formativas" in contenido
    assert "Evaluación:" in contenido or "Cuestionario" in contenido or "Evaluación" in contenido

    # Cambiar estado
    resp_ev = client.post(
        "/admin/evaluaciones/1/estado",
        data={"estado": "borrador"},
        follow_redirects=True,
    )
    assert resp_ev.status_code == 200

    # Restaurar
    client.post("/admin/evaluaciones/1/estado", data={"estado": "publicado"}, follow_redirects=True)
