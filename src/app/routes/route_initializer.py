# route_initializer.py

from flask_wtf.csrf import CSRFProtect

from .index import create_index_blueprint
from .search_objects import create_search_objects_blueprint


def initialize_routes(
    app,
    route,
    calculate_camera_fov,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    get_alt_az,
    get_object_data,
    count_dso,
):
    index_bp = create_index_blueprint(
        route,
        calculate_camera_fov,
        get_object_data,
        get_alt_az,
        calculate_max_shooting_time,
        calculate_number_of_shoots,
        count_dso,
    )
    search_objects_bp = create_search_objects_blueprint(route)

    app.register_blueprint(index_bp)
    app.register_blueprint(search_objects_bp)
    csrf = CSRFProtect()
    csrf.init_app(app)
