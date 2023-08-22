from datetime import datetime
from flask import jsonify, render_template, request

from data import dsoDict, jsonObjectList, initialize
from forms import ObjectForm
import settings
from astropy.coordinates import EarthLocation
import astropy.units as u
from logger import log_exceptions


def initialize_routes(
    app,
    calculate_camera_fov,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    get_alt_az,
    get_object_data,
):
    @app.route(f"{settings.ROUTE}/search_objects")
    @log_exceptions(app)
    def search_objects():
        if len(dsoDict) == 0:
            initialize()

        query = request.args.get("query")
        if len(query) < 3:
            return jsonify([])

        results = [
            obj
            for obj_id, obj in dsoDict.items()
            if query.lower() in str(obj_id).lower()
            or query.lower() in obj["name"].lower()
        ]

        suggestions = [
            {
                "name": f"{obj['name']} ({obj.get('other identifiers', {}).get('common names', ['No common name'])[0]})",
                "id": obj["id"],
            }
            for obj in results
        ]

        return jsonify(suggestions)

    @app.route(settings.ROUTE, methods=["GET", "POST"])
    @log_exceptions(app)
    def index():
        form = ObjectForm()
        if form.validate_on_submit():
            object_name = form.object_name.data
            latitude = form.latitude.data
            longitude = form.longitude.data
            sensor_height_mm = form.sensor_height_mm.data
            sensor_width_mm = form.sensor_width_mm.data
            focal_length = form.focal_length.data
            utc_datetime = datetime.utcnow()
            shoot_interval = form.shoot_interval.data
            aperture = form.aperture.data
            number_of_pixels_in_width = form.number_of_pixels_in_width.data
            number_of_pixels_in_height = form.number_of_pixels_in_height.data
            camera_position = form.camera_position.data
            object_id = form.object_id.data

            ra, dec, size_major, size_minor, object_name, pa, error = get_object_data(
                object_id
            )
            if error:
                return render_template("error.html", error=error)

            location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg)
            altaz = get_alt_az(location, ra, dec, utc_datetime)
            if altaz is None:
                return render_template(
                    "error.html",
                    error=f"Altitude and azimuth not found for {object_name} ",
                )

            fov_width, fov_height, pixel_width, pixel_height = calculate_camera_fov(
                sensor_width_mm,
                sensor_height_mm,
                number_of_pixels_in_width,
                number_of_pixels_in_height,
                focal_length,
            )
            max_shooting_time, real_max_shooting_time = calculate_max_shooting_time(
                aperture, sensor_width_mm, number_of_pixels_in_width, focal_length
            )
            num_shoots = calculate_number_of_shoots(
                altaz,
                location,
                ra,
                dec,
                fov_width,
                fov_height,
                size_major,
                size_minor,
                max_shooting_time,
                shoot_interval,
                camera_position,
                pa,
            )

            if num_shoots is None:
                return render_template(
                    "error.html",
                    error=f"Object {object_name} number of shoots could be not calculated.",
                )

            return render_template(
                "result.html",
                fov_width=fov_width,
                fov_height=fov_height,
                pixel_width=pixel_width,
                pixel_height=pixel_height,
                size_major=size_major,
                size_minor=size_minor,
                max_shooting_time=max_shooting_time,
                num_shoots=num_shoots,
                object_name=object_name,
                real_max_shooting_time=real_max_shooting_time,
                pa=pa,
                camera_position=camera_position,
                route=settings.ROUTE,
                db_num_objects=len(jsonObjectList),
                error=None,
            )

        return render_template(
            "index.html",
            error=form.errors,
            route=settings.ROUTE,
            db_num_objects=len(jsonObjectList),
        )
