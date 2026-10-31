from flask import Flask

from config import INSTANCE_DIR, Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config) -> Flask:
    INSTANCE_DIR.mkdir(exist_ok=True)

    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),
        instance_relative_config=True,
    )
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id: str):
        if not user_id.isdigit():
            return None
        return db.session.get(Usuario, int(user_id))

    from app.routes import main_bp
    from app.routes.aprendizaje import aprendizaje_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(aprendizaje_bp)

    with app.app_context():
        from app import models  # noqa: F401
        from app.seeds import (
            seed_actividades_iniciales,
            seed_contenidos_iniciales,
            seed_usuarios_iniciales,
        )

        db.create_all()
        _seed_roles()
        seed_contenidos_iniciales()
        seed_usuarios_iniciales()
        seed_actividades_iniciales()

    return app


def _seed_roles() -> None:
    from sqlalchemy import select

    from app.models import Rol

    existentes = {rol.nombre for rol in db.session.scalars(select(Rol)).all()}
    iniciales = [
        Rol(nombre="ciudadano", descripcion="Usuario público de la plataforma educativa."),
        Rol(nombre="administrador", descripcion="Gestiona contenidos, actividades y evaluaciones."),
    ]
    for rol in iniciales:
        if rol.nombre not in existentes:
            db.session.add(rol)
    db.session.commit()
