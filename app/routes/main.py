from flask import render_template

from app.routes import main_bp


@main_bp.get("/")
def index():
    return render_template("index.html")
