import os

from apiflask import APIFlask

from .api.v1 import api_v1 as api_v1_blueprint
from .status import status as status_blueprint


def create_app():
    """
    Implement application factory method
    info: https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/
    """
    app = APIFlask(
        __name__, title="API Nationaal wegenbestand", version="0.4.1"
    )

    # Config
    SECRET_KEY = os.environ.get("APP_SECRET", default=None)
    if not SECRET_KEY:
        raise ValueError("No secret key set for Flask application")

    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.config["DB_NAME"] = os.environ.get("DB_NAME")
    app.config["DB_USER"] = os.environ.get("DB_USER")
    app.config["DB_PWD"] = os.environ.get("DB_PWD")
    app.config["DB_HOST"] = os.environ.get("DB_HOST")
    app.config["DB_PORT"] = os.environ.get("DB_PORT")
    app.config["DB_SSL"] = os.environ.get("DB_SSL")

    # register database commands
    from . import db

    db.init_app(app)

    app.register_blueprint(api_v1_blueprint, url_prefix="/v1")
    app.register_blueprint(status_blueprint, url_prefix="/status")

    return app
