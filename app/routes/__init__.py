from flask import Blueprint

main_bp = Blueprint("main", __name__)

from app.routes import main  # noqa: E402, F401
