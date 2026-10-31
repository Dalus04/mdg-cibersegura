"""Pruebas automatizadas de la API REST v1 de MDG Cibersegura."""

from sqlalchemy import select

from app.extensions import db
from app.models import Rol, Usuario


def _obtener_credenciales_admin():
    return "admin@guadalupe.gob.pe", "Admin1234!"


def _obtener_credenciales_ciudadano():
    return "ciudadano@ejemplo.com", "Ciudadano123!"


def test_api_index(client):
    """Verifica que el índice de la API devuelva la especificación y metadatos JSON."""
    resp = client.get("/api/v1/")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["version"] == "1.0.0"
    assert "endpoints" in data
    assert "Municipalidad Distrital de Guadalupe" in data["institucion"]


def test_api_salud(client):
    """Verifica el endpoint de salud del sistema."""
    resp = client.get("/api/v1/salud")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["estado"] == "saludable"
    assert "timestamp_utc" in data


def test_api_auth_login_fallido(client):
    """Verifica que el login con credenciales erróneas retorne 401 JSON."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"correo": "noexiste@test.com", "password": "ClaveIncorrecta1!"},
    )
    assert resp.status_code == 401
    assert resp.is_json
    data = resp.get_json()
    assert data["exito"] is False
    assert data["codigo"] == "credenciales_invalidas"


def test_api_auth_login_campos_faltantes(client):
    """Verifica que omitir correo o contraseña retorne 400 Bad Request."""
    resp = client.post("/api/v1/auth/login", json={"correo": "admin@guadalupe.gob.pe"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["codigo"] == "campos_requeridos"


def test_api_auth_login_y_yo(client):
    """Verifica login exitoso y consulta del endpoint /api/v1/auth/yo."""
    # Sin sesión previa
    resp_anon = client.get("/api/v1/auth/yo")
    assert resp_anon.status_code == 401

    # Login
    correo, password = _obtener_credenciales_ciudadano()
    resp_login = client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "password": password},
    )
    assert resp_login.status_code == 200
    datos_login = resp_login.get_json()
    assert datos_login["exito"] is True
    assert datos_login["usuario"]["correo"] == correo
    assert datos_login["usuario"]["rol"] == "ciudadano"
    assert datos_login["usuario"]["es_administrador"] is False

    # Consulta con sesión
    resp_yo = client.get("/api/v1/auth/yo")
    assert resp_yo.status_code == 200
    datos_yo = resp_yo.get_json()
    assert datos_yo["usuario"]["correo"] == correo


def test_api_auth_registro_ciudadano(client):
    """Verifica el registro de un nuevo ciudadano mediante la API."""
    payload = {
        "nombres": "Roberto",
        "apellidos": "Alvarado",
        "correo": "roberto.alvarado@test.com",
        "password": "Password123!",
    }
    resp = client.post("/api/v1/auth/registro", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["exito"] is True
    assert data["usuario"]["correo"] == "roberto.alvarado@test.com"

    # Intento de duplicado
    resp_dup = client.post("/api/v1/auth/registro", json=payload)
    assert resp_dup.status_code == 409


def test_api_auth_logout(client):
    """Verifica que logout limpie la sesión."""
    correo, password = _obtener_credenciales_ciudadano()
    client.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    assert client.get("/api/v1/auth/yo").status_code == 200

    resp_logout = client.post("/api/v1/auth/logout")
    assert resp_logout.status_code == 200
    assert client.get("/api/v1/auth/yo").status_code == 401


def test_api_temas_catalogo(client):
    """Verifica la consulta del catálogo de temas."""
    resp = client.get("/api/v1/temas")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["exito"] is True
    assert data["total"] > 0
    assert "temas" in data

    primer_tema = data["temas"][0]
    assert "id_tema" in primer_tema
    assert "titulo" in primer_tema
    assert primer_tema["total_lecciones"] > 0


def test_api_tema_detalle(client):
    """Verifica la consulta detallada de un tema publicado."""
    resp = client.get("/api/v1/temas/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["exito"] is True
    tema = data["tema"]
    assert tema["id_tema"] == 1
    assert len(tema["contenidos"]) > 0
    assert len(tema["actividades"]) > 0
    assert tema["evaluacion"] is not None


def test_api_tema_inexistente(client):
    """Verifica que un tema inexistente retorne 404 JSON."""
    resp = client.get("/api/v1/temas/99999")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["codigo"] == "tema_no_encontrado"


def test_api_contenido_lectura_y_progreso(client):
    """Verifica la lectura de una lección y la acción de marcar completado."""
    resp_leccion = client.get("/api/v1/temas/1/contenidos/1")
    assert resp_leccion.status_code == 200
    data_leccion = resp_leccion.get_json()
    assert data_leccion["exito"] is True
    assert len(data_leccion["contenido"]["parrafos"]) > 0
    assert data_leccion["contenido"]["esta_completada"] is False

    # Intentar marcar completado sin autenticación -> 401
    resp_unauth = client.post("/api/v1/temas/1/contenidos/1/completar", json={"completado": True})
    assert resp_unauth.status_code == 401

    # Login ciudadano
    correo, password = _obtener_credenciales_ciudadano()
    client.post("/api/v1/auth/login", json={"correo": correo, "password": password})

    # Marcar completado con sesión
    resp_comp = client.post("/api/v1/temas/1/contenidos/1/completar", json={"completado": True})
    assert resp_comp.status_code == 200
    assert resp_comp.get_json()["completado"] is True

    # Verificar que ahora figure completada en la lectura
    resp_ver = client.get("/api/v1/temas/1/contenidos/1")
    assert resp_ver.get_json()["contenido"]["esta_completada"] is True

    # Desmarcar
    resp_des = client.post("/api/v1/temas/1/contenidos/1/completar", json={"completado": False})
    assert resp_des.status_code == 200
    assert resp_des.get_json()["completado"] is False


def test_api_actividad_sanitizada_y_resolucion(client):
    """Verifica que las opciones de una actividad no expongan respuestas y que la resolución funcione."""
    resp_act = client.get("/api/v1/temas/1/actividades/1")
    assert resp_act.status_code == 200
    data_act = resp_act.get_json()
    act = data_act["actividad"]
    assert len(act["opciones"]) > 0
    for opt in act["opciones"]:
        assert "es_correcta" not in opt
        assert "explicacion" not in opt

    # Resolver sin autenticación -> 401
    resp_unauth = client.post(
        "/api/v1/temas/1/actividades/1/resolver",
        json={"opcion_id": "opt_3"},
    )
    assert resp_unauth.status_code == 401

    # Login
    correo, password = _obtener_credenciales_ciudadano()
    client.post("/api/v1/auth/login", json={"correo": correo, "password": password})

    # Resolver opción requerida omitida -> 400
    resp_bad = client.post("/api/v1/temas/1/actividades/1/resolver", json={})
    assert resp_bad.status_code == 400

    # Resolver correctamente
    resp_res = client.post(
        "/api/v1/temas/1/actividades/1/resolver",
        json={"opcion_id": "opt_3"},
    )
    assert resp_res.status_code == 200
    res_data = resp_res.get_json()
    assert res_data["exito"] is True
    assert res_data["es_correcta"] is True
    assert res_data["resultado_clave"] == "exitoso"


def test_api_evaluacion_cuestionario_y_calificacion(client):
    """Verifica el cuestionario de evaluación, la calificación formal y el desglose de resultados."""
    # Consultar evaluación: alternativas no deben incluir 'es_correcta'
    resp_eval = client.get("/api/v1/temas/1/evaluacion")
    assert resp_eval.status_code == 200
    eval_json = resp_eval.get_json()["evaluacion"]
    assert len(eval_json["preguntas"]) > 0
    for preg in eval_json["preguntas"]:
        for alt in preg["alternativas"]:
            assert "es_correcta" not in alt

    # Enviar respuestas sin login -> 401
    resp_unauth = client.post("/api/v1/temas/1/evaluacion/enviar", json={"respuestas": {}})
    assert resp_unauth.status_code == 401

    # Login
    correo, password = _obtener_credenciales_ciudadano()
    client.post("/api/v1/auth/login", json={"correo": correo, "password": password})

    # Enviar con respuestas incompletas -> 400
    resp_incomp = client.post(
        "/api/v1/temas/1/evaluacion/enviar",
        json={"respuestas": {str(eval_json["preguntas"][0]["id_pregunta"]): 1}},
    )
    assert resp_incomp.status_code == 400

    # Obtener alternativas correctas directamente de la BD para responder con nota perfecta
    from app.models import Alternativa

    respuestas_correctas = {}
    for preg in eval_json["preguntas"]:
        alt_ok = db.session.scalar(
            select(Alternativa).where(
                Alternativa.id_pregunta == preg["id_pregunta"],
                Alternativa.es_correcta.is_(True),
            )
        )
        assert alt_ok is not None
        respuestas_correctas[str(preg["id_pregunta"])] = alt_ok.id_alternativa

    resp_envio = client.post(
        "/api/v1/temas/1/evaluacion/enviar",
        json={"respuestas": respuestas_correctas},
    )
    assert resp_envio.status_code == 201
    datos_envio = resp_envio.get_json()
    assert datos_envio["exito"] is True
    assert datos_envio["intento"]["aprobado"] is True
    id_intento = datos_envio["intento"]["id_intento_evaluacion"]

    # Consultar resultado del intento
    resp_res = client.get(f"/api/v1/temas/1/evaluacion/resultado/{id_intento}")
    assert resp_res.status_code == 200
    res_json = resp_res.get_json()["resultado"]
    assert res_json["aprobado"] is True
    assert len(res_json["desglose"]) == len(eval_json["preguntas"])


def test_api_mi_progreso(client):
    """Verifica que /api/v1/progreso/mi-progreso devuelva las métricas del ciudadano autenticado."""
    # Sin login -> 401
    assert client.get("/api/v1/progreso/mi-progreso").status_code == 401

    # Con login
    correo, password = _obtener_credenciales_ciudadano()
    client.post("/api/v1/auth/login", json={"correo": correo, "password": password})

    resp = client.get("/api/v1/progreso/mi-progreso")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["exito"] is True
    assert "resumen" in data
    resumen = data["resumen"]
    assert "total_lecciones" in resumen
    assert "porcentaje_global" in resumen
    assert len(resumen["temas"]) > 0


def test_api_admin_control_de_acceso(client):
    """Verifica que los endpoints administrativos exijan rol de administrador."""
    # 1. Sin autenticación -> 401
    resp_anon = client.get("/api/v1/admin/metricas")
    assert resp_anon.status_code == 401
    assert resp_anon.get_json()["codigo"] == "no_autenticado"

    # 2. Con cuenta de ciudadano -> 403 Acceso denegado
    correo, password = _obtener_credenciales_ciudadano()
    client.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    resp_ciudadano = client.get("/api/v1/admin/metricas")
    assert resp_ciudadano.status_code == 403
    assert resp_ciudadano.get_json()["codigo"] == "acceso_denegado"


def test_api_admin_metricas_y_gestion(client):
    """Verifica los endpoints administrativos con sesión de administrador."""
    # Login como administrador institucional
    admin_correo, admin_pass = _obtener_credenciales_admin()
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"correo": admin_correo, "password": admin_pass},
    )
    assert login_resp.status_code == 200
    assert login_resp.get_json()["usuario"]["es_administrador"] is True

    # 1. Métricas generales
    resp_met = client.get("/api/v1/admin/metricas")
    assert resp_met.status_code == 200
    metricas = resp_met.get_json()["metricas"]
    assert metricas["usuarios"]["total"] >= 2
    assert metricas["contenidos"]["total_temas"] > 0
    assert metricas["actividades"]["total_actividades"] > 0
    assert metricas["evaluaciones"]["total_evaluaciones"] > 0

    # 2. Listar usuarios
    resp_usr = client.get("/api/v1/admin/usuarios")
    assert resp_usr.status_code == 200
    usuarios = resp_usr.get_json()["usuarios"]
    assert len(usuarios) >= 2

    # 3. Cambiar estado de usuario (desactivar ciudadano)
    ciudadano_obj = next((u for u in usuarios if u["rol"] == "ciudadano"), None)
    assert ciudadano_obj is not None
    resp_des = client.patch(
        f"/api/v1/admin/usuarios/{ciudadano_obj['id_usuario']}/estado",
        json={"estado": "inactivo"},
    )
    assert resp_des.status_code == 200
    assert resp_des.get_json()["estado"] == "inactivo"

    # Reactivar
    resp_act = client.patch(
        f"/api/v1/admin/usuarios/{ciudadano_obj['id_usuario']}/estado",
        json={"estado": "activo"},
    )
    assert resp_act.status_code == 200

    # Intentar auto-desactivar la propia cuenta admin -> debe fallar con 400
    admin_obj = next((u for u in usuarios if u["rol"] == "administrador"), None)
    assert admin_obj is not None
    resp_auto = client.patch(
        f"/api/v1/admin/usuarios/{admin_obj['id_usuario']}/estado",
        json={"estado": "inactivo"},
    )
    assert resp_auto.status_code == 400

    # 4. Contenidos y cambio de estado
    resp_cont = client.get("/api/v1/admin/contenidos")
    assert resp_cont.status_code == 200
    assert len(resp_cont.get_json()["temas"]) > 0

    resp_tema_est = client.patch("/api/v1/admin/temas/1/estado", json={"estado": "borrador"})
    assert resp_tema_est.status_code == 200
    assert resp_tema_est.get_json()["estado"] == "borrador"

    # Restaurar a publicado
    client.patch("/api/v1/admin/temas/1/estado", json={"estado": "publicado"})

    # 5. Actividades y evaluaciones
    resp_act = client.get("/api/v1/admin/actividades")
    assert resp_act.status_code == 200
    assert len(resp_act.get_json()["actividades"]) > 0

    resp_ev = client.get("/api/v1/admin/evaluaciones")
    assert resp_ev.status_code == 200
    assert len(resp_ev.get_json()["evaluaciones"]) > 0
