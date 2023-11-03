import os

from flask import Flask

from app.routes.route_initializer import initialize_routes
from app.utils.astro_utils import get_object_data, count_dso
from app.utils.calculations import (
    calculate_camera_fov,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
)
from app.utils.camera_utils import load_cameras_from_json
from app.utils.initialize import init_limiter, init_logging, init_talisman
from app.utils.settings import load_config
from flask_wtf.csrf import CSRFProtect


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
    config = load_config()

    ROUTE = config["route"]
    SECRET_KEY = config["SECRET_KEY"]
    STATIC_URL_PATH = config["STATIC_URL_PATH"]
    DEBUG = config["DEBUG"]

    app = Flask(
        __name__,
        static_url_path=STATIC_URL_PATH,
        static_folder="static",
        template_folder="templates",
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG

    CSRFProtect(app)  # Initialize CSRF protection here

    init_logging(app)
    init_limiter(app)
    init_talisman(app)

    app.jinja_env.filters["format_float"] = format_float

    current_directory = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_directory, "db", "cameras-all.json")

    cameras = load_cameras_from_json(json_path)

    initialize_routes(
        app,
        ROUTE,
        calculate_camera_fov,
        calculate_max_shooting_time,
        calculate_number_of_shoots,
        get_object_data,
        count_dso,
        cameras,
    )

    if app.debug:
        app.run()

    return app
