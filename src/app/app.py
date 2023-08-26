from flask import Flask

from app.utils.initialize import init_csrf, init_limiter, init_logging, init_talisman
from app.routes.route_initializer import initialize_routes
from app.utils.calculations import (
    calculate_camera_fov,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
)
from app.utils.astro_utils import get_alt_az, get_object_data, count_dso

from app.utils.settings import load_config

config = load_config()

ROUTE = config["ROUTE"]
SECRET_KEY = config["SECRET_KEY"]
STATIC_URL_PATH = config["STATIC_URL_PATH"]
DEBUG = config["DEBUG"]
pass


def format_float(value, format_spec=".2f"):
    """
    Format the given float value using the specified format specification.

    Parameters:
        value (float): The float value to be formatted.
        format_spec (str): The format specification used to format the value. Defaults to ".2f".

    Returns:
        str: The formatted float value.
    """
    return format(value, format_spec)


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        app (Flask): The Flask application object.
    """
    app = Flask(
        __name__,
        static_url_path=STATIC_URL_PATH,
        static_folder="static",
        template_folder="templates",
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG

    app.dsoDict = {}
    app.jsonObjectList = []

    init_logging(app)
    init_limiter(app)
    init_talisman(app)
    init_csrf(app)

    app.jinja_env.filters["format_float"] = format_float

    return app


app = create_app()
initialize_routes(
    app,
    ROUTE,
    calculate_camera_fov,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    get_alt_az,
    get_object_data,
    count_dso,
)


if __name__ == "__main__":
    app.run(debug=DEBUG)
