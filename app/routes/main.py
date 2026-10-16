from flask import render_template
from sqlalchemy import inspect, select

from app.extensions import db
from app.models import Rol
from app.routes import main_bp


@main_bp.get("/")
def index():
    inspector = inspect(db.engine)
    tablas = inspector.get_table_names()
    roles = db.session.scalars(select(Rol).order_by(Rol.id_rol)).all()
    return render_template(
        "index.html",
        tablas=tablas,
        roles=roles,
    )
