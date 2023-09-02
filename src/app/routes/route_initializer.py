# route_initializer.py

from flask_wtf.csrf import CSRFProtect

from .cameras import create_camera_blueprint
from .index import create_index_blueprint
from .search_objects import create_search_objects_blueprint


def initialize_routes(
    app,
    route,
    calculate_camera_fov,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    get_object_data,
    count_dso,
    cameras,
):
    index_bp = create_index_blueprint(
        app,
        route,
        calculate_camera_fov,
        get_object_data,
        calculate_max_shooting_time,
        calculate_number_of_shoots,
        count_dso,
    )
    search_objects_bp = create_search_objects_blueprint(app, route)

    camera_bp = create_camera_blueprint(app, route, cameras)

    app.register_blueprint(index_bp)
    app.register_blueprint(search_objects_bp)
    app.register_blueprint(camera_bp)
    csrf = CSRFProtect()
    csrf.init_app(app)
