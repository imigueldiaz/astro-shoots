from flask import Blueprint, render_template, request

from app.forms.forms import ObjectForm

from app.utils.calculation_service import perform_astro_calculations


def create_index_blueprint(
    ROUTE,
    calculate_camera_fov,
    get_object_data,
    get_alt_az,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
):
    index_bp = Blueprint("index", __name__)

    @index_bp.route(ROUTE, methods=["GET", "POST"])
    def index():
        form = ObjectForm()
        # form.object_id.data = request.args.get("object_id", "")
        if form.validate_on_submit():
            form_data = {
                field_name: getattr(form, field_name).data
                for field_name in form._fields
            }

            result = perform_astro_calculations(
                form_data,
                calculate_camera_fov,
                get_object_data,
                get_alt_az,
                calculate_max_shooting_time,
                calculate_number_of_shoots,
                ROUTE,
            )

            if result.get("error"):
                error = result["error"]
                return render_template("error.html", error=error)

            return render_template("result.html", **result)

        return render_template(
            "index.html", form=form, route=ROUTE
        )  # Pass the form object

    return index_bp
