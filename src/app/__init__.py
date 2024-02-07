from apiflask import APIFlask

from ..config.settings import app_name, app_version
from .api.v1 import api_v1 as api_v1_blueprint
from .status import status as status_blueprint


def create_app():
    """
    Create application using the app factory pattern.
    """
    app = APIFlask(__name__, title=app_name, version=app_version)

    app.config.from_object("src.config.settings")

    # register database commands
    from . import db

    db.init_app(app)

    app.register_blueprint(api_v1_blueprint, url_prefix="/v1")
    app.register_blueprint(status_blueprint, url_prefix="/status")

    return app
