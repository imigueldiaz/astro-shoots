from typing import Callable

from flask import Blueprint, render_template, request

from app.forms.forms import ObjectForm
from app.utils.calculation_service import perform_astro_calculations


def create_index_blueprint(
    route: str,
    calculate_camera_fov: Callable,
    get_object_data: Callable,
    get_alt_az: Callable,
    calculate_max_shooting_time: Callable,
    calculate_number_of_shoots: Callable,
    count_dso: Callable,
) -> Blueprint:
    index_bp: Blueprint = Blueprint("index", __name__)

    @index_bp.route(route, methods=["GET", "POST"])
    def index():
        form = ObjectForm()
        if form.validate_on_submit():
            form_data = {
                field_name: getattr(form, field_name).data for field_name in form.fields
            }

            result = perform_astro_calculations(
                form_data,
                calculate_camera_fov,
                get_object_data,
                calculate_max_shooting_time,
                calculate_number_of_shoots,
                route,
            )

            if result.get("error"):
                error = result["error"]
                return render_template("error.html", error=error)

            return render_template("result.html", **result)

        return render_template(
            "index.html",
            form=form,
            route=route,
            cookies=request.cookies,
            db_num_objects=count_dso(),
        )  # Pass the form object

    return index_bp
