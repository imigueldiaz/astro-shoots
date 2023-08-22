import configparser
import json
import logging
import math
import os
from datetime import datetime, timedelta
from functools import wraps

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_talisman import Talisman
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from pyongc import ongc

# Additional imports for input validation and rate limiting
from wtforms import (
    FloatField,
    HiddenField,
    IntegerField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, InputRequired, NumberRange

# Load environment variables from .env file
load_dotenv()

# Read the configuration file
config = configparser.ConfigParser()
config.read("config.ini")

# Get the route and static_url_path from the configuration file
route = config.get("APP", "ROUTE")
static_url_path = config.get("APP", "STATIC_URL_PATH")

app = Flask(__name__, static_url_path=static_url_path)

# Add logging configuration
handler = logging.FileHandler("app.log")
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Set the secret key for your Flask application
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["DEBUG"] = True

# Add rate limiting
limiter = Limiter(app, default_limits=["10000 per day", "2000 per hour"])

csp = {
    "default-src": "'self'",
    "img-src": ["*", "data:"],
    "script-src": "'self' 'unsafe-inline'",
    "style-src": "'self' 'unsafe-inline'",
    "font-src": "'self'",
}

talisman = Talisman(app, content_security_policy=csp)
csrf = CSRFProtect(app)

# Get the object list
obj_list = ongc.listObjects()


# Define a custom function to filter out key-value pairs with a None value
def filter_none(d):
    return {k: v for k, v in d.items() if v is not None}


# Convert each object to JSON and store it in a global list, filtering out None values
json_obj_list = [json.loads(obj.to_json(), object_hook=filter_none) for obj in obj_list]

obj_dict = {}
for json_obj in json_obj_list:
    # Add primary ID first
    obj_dict[json_obj["id"]] = json_obj

    # Check for other identifiers
    if "other identifiers" in json_obj:
        # Add each identifier
        for id_type, id_value in json_obj["other identifiers"].items():
            if id_value is not None:
                if isinstance(id_value, list):
                    for identifier in id_value:
                        if identifier is not None:
                            obj_dict[identifier] = json_obj
                else:
                    obj_dict[id_value] = json_obj


class ObjectForm(FlaskForm):
    object_name = StringField("Object Name", validators=[DataRequired()])
    latitude = FloatField(
        "Latitude", validators=[InputRequired(), NumberRange(-90, 90)]
    )
    longitude = FloatField(
        "Longitude", validators=[InputRequired(), NumberRange(-180, 180)]
    )
    sensor_height_mm = FloatField(
        "Sensor Height (mm)", validators=[DataRequired(), NumberRange(1, 100)]
    )
    sensor_width_mm = FloatField(
        "Sensor Width (mm)", validators=[DataRequired(), NumberRange(1, 100)]
    )
    focal_length = FloatField(
        "Focal Length", validators=[DataRequired(), NumberRange(1, 10000)]
    )
    shoot_interval = FloatField(
        "Shoot Interval", validators=[InputRequired(), NumberRange(0, 999)]
    )
    aperture = FloatField(
        "Aperture", validators=[InputRequired(), NumberRange(0.8, 64)]
    )
    number_of_pixels_in_width = IntegerField(
        "Width px", validators=[DataRequired(), NumberRange(1, 9999)]
    )
    number_of_pixels_in_height = IntegerField(
        "Height px", validators=[DataRequired(), NumberRange(1, 9999)]
    )

    camera_position = IntegerField(
        "Camera Position", validators=[InputRequired(), NumberRange(-90, 90)]
    )
    object_id = HiddenField()
    submit = SubmitField("Submit")


def format_float(value, format_spec=".2f"):
    return format(value, format_spec)


app.jinja_env.filters["format_float"] = format_float


def log_exceptions(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.exception("An error occurred: %s", str(e))
            return "An error occurred. Please check the logs for more information.", 500

    return wrapped


@app.route(f"{route}/search_objects")
def search_objects():
    query = request.args.get("query")
    if len(query) < 3:
        return jsonify([])

    results = [
        obj
        for obj_id, obj in obj_dict.items()
        if query.lower() in str(obj_id).lower() or query.lower() in obj["name"].lower()
    ]

    suggestions = [
        {
            "name": f"{obj['name']} ({obj.get('other identifiers', {}).get('common names', ['No common name'])[0]})",
            "id": obj["id"],
        }
        for obj in results
    ]

    return jsonify(suggestions)


@app.route(route, methods=["GET", "POST"])
@limiter.limit("10 per minute")
@log_exceptions
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
                "error.html", error=f"Altitude and azimuth not found for {object_name} "
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
            route=route,
            db_num_objects=len(obj_list),
            error=None,
        )

    return render_template(
        "index.html",
        error=form.errors,
        route=route,
        db_num_objects=len(obj_list),
    )


def get_object_data(object_id):
    result = obj_dict.get(object_id)

    if result is None:
        try:
            object_id_int = int(object_id)
            result = obj_dict.get(object_id_int)  # Try the integer version
        except ValueError:
            pass  # The ID could not be converted to an integer

    if result is None:
        return None, None, None, None, None, None, f"Object {object_id} not found"

    ra_hms = result["coordinates"]["right ascension"]
    dec_dms = result["coordinates"]["declination"]

    # Create a SkyCoord object using the HMS and DMS values
    coord = SkyCoord(ra=ra_hms, dec=dec_dms, unit=(u.hourangle, u.deg))

    ra = coord.ra.deg
    dec = coord.dec.deg

    # Find the common name among the identifiers
    common_name = result["name"]

    if common_name:
        object_id = f"{object_id} ({common_name})"
    else:
        object_id = f"{object_id}"

    size_major = result["dimensions"]["major axis"]
    size_minor = result["dimensions"]["minor axis"]
    pa = result["dimensions"]["position angle"]

    if pa is None:
        pa = 0

    if size_major is None or size_minor is None:
        return (
            None,
            None,
            None,
            None,
            None,
            None,
            f"Size data is missing for {object_id}",
        )

    return ra, dec, size_major, size_minor, object_id, pa, None


def get_alt_az(location, ra, dec, utc_datetime=None, min_altitude=0, min_speed=0.1):
    if utc_datetime is None:
        utc_datetime = datetime.utcnow()
    obj = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))

    while True:
        altaz = obj.transform_to(AltAz(location=location, obstime=Time(utc_datetime)))
        if (altaz.alt.degree > min_altitude).any():
            next_time = utc_datetime + timedelta(minutes=1)
            next_altaz = obj.transform_to(
                AltAz(location=location, obstime=Time(next_time))
            )
            avg_altitude_speed = (next_altaz.alt.degree - altaz.alt.degree) * 60
            avg_azimuth_speed = (next_altaz.az.degree - altaz.az.degree) * 60

            if avg_altitude_speed > min_speed and avg_azimuth_speed > min_speed:
                break

        utc_datetime += timedelta(minutes=1)

    return altaz


def calculate_camera_fov(
    sensor_width_mm,
    sensor_height_mm,
    horizontal_pixels,
    vertical_pixels,
    focal_length_mm,
):
    pixel_width_mm = sensor_width_mm / horizontal_pixels
    pixel_height_mm = sensor_height_mm / vertical_pixels

    fov_horizontal_degrees = 2 * math.degrees(
        math.atan((pixel_width_mm * horizontal_pixels) / (2 * focal_length_mm))
    )
    fov_vertical_degrees = 2 * math.degrees(
        math.atan((pixel_height_mm * vertical_pixels) / (2 * focal_length_mm))
    )

    fov_horizontal_arcminutes = fov_horizontal_degrees * 60
    fov_vertical_arcminutes = fov_vertical_degrees * 60

    pixel_width_arcsec = fov_horizontal_arcminutes / horizontal_pixels * 60
    pixel_height_arcsec = fov_vertical_arcminutes / vertical_pixels * 60

    return (
        fov_horizontal_arcminutes,
        fov_vertical_arcminutes,
        pixel_width_arcsec,
        pixel_height_arcsec,
    )


def round_down_shutter_speed(shutter_speed):
    standard_shutter_speeds = [
        1 / 8000,
        1 / 6400,
        1 / 5000,
        1 / 4000,
        1 / 3200,
        1 / 2500,
        1 / 2000,
        1 / 1600,
        1 / 1250,
        1 / 1000,
        1 / 800,
        1 / 640,
        1 / 500,
        1 / 400,
        1 / 320,
        1 / 250,
        1 / 200,
        1 / 160,
        1 / 125,
        1 / 100,
        1 / 80,
        1 / 60,
        1 / 50,
        1 / 40,
        1 / 30,
        1 / 25,
        1 / 20,
        1 / 15,
        1 / 13,
        1 / 10,
        1 / 8,
        1 / 6,
        1 / 5,
        1 / 4,
        0.3,
        0.4,
        0.5,
        0.6,
        0.8,
        1,
        1.3,
        1.6,
        2,
        2.5,
        3,
        4,
        5,
        6,
        8,
        10,
        13,
        15,
        20,
        25,
        30,
    ]

    rounded_shutter_speed = min(
        standard_shutter_speeds,
        key=lambda x: abs(x - shutter_speed) if x <= shutter_speed else float("inf"),
    )
    return rounded_shutter_speed


def calculate_max_shooting_time(
    aperture, sensor_width_mm, number_of_pixels_in_width, focal_length
):
    pixel_pitch = (sensor_width_mm / number_of_pixels_in_width) * 1000  # in microns
    shutter_speed = (35 * aperture + 30 * pixel_pitch) / focal_length  # in seconds

    rounded_shutter_speed = round_down_shutter_speed(shutter_speed)
    return rounded_shutter_speed, shutter_speed


def calculate_number_of_shoots(
    altaz,
    location,
    ra,
    dec,
    fov_width,
    fov_height,
    size_major,
    size_minor,
    exposure_time,
    shoot_interval,
    camera_position,
    PA,
):
    if np.ma.is_masked(size_major) or np.ma.is_masked(size_minor):
        app.logger.error("Size data is missing for the object")
        return None

    # Aplicar rotaciones a FOV
    if camera_position == 0:
        fov_rot_h = fov_width
        fov_rot_v = fov_height

    elif camera_position == 90:
        fov_rot_h = fov_height
        fov_rot_v = fov_width

    elif camera_position == -90:
        fov_rot_h = fov_height
        fov_rot_v = fov_width

    else:
        fov_rot_h, fov_rot_v = rotate_fov(fov_width, fov_height, camera_position, PA)

    available_altitude = abs(fov_rot_h - size_major) / 2
    available_azimuth = abs(fov_rot_v - size_minor) / 2
    current_time = altaz.obstime
    num_shoots = 0
    while True:
        # Calculate the new position of the object after shoot_interval and exposure_time
        next_time = current_time + (shoot_interval + exposure_time) * u.second
        new_altaz = get_alt_az(location, ra, dec, next_time)
        avg_altitude_speed = (
            abs(new_altaz.alt.degree - altaz.alt.degree) * 60 / shoot_interval
        )
        avg_azimuth_speed = (
            abs(new_altaz.az.degree - altaz.az.degree) * 60 / shoot_interval
        )
        max_movement_altitude = available_altitude / abs(avg_altitude_speed)
        max_movement_azimuth = available_azimuth / abs(avg_azimuth_speed)
        total_time_available = (
            min(max_movement_altitude, max_movement_azimuth) * shoot_interval
        )  # Convert minutes to seconds
        total_time_per_shot = exposure_time + shoot_interval
        num_shots = max(0, total_time_available // total_time_per_shot)
        if num_shots > 0:
            break
        current_time = next_time
        altaz = new_altaz
    return num_shots


def rotate_fov(fov_width, fov_height, camera_position, PA):
    # Convertir ángulos a radianes
    PA_rad = PA * np.pi / 180

    camera_rot_rad = camera_position * np.pi / 180

    # Calcular componentes de rotación
    CP_sin = np.sin(camera_rot_rad)
    CP_cos = np.cos(camera_rot_rad)

    PA_sin = np.sin(PA_rad)
    PA_cos = np.cos(PA_rad)
    # Matriz de rotación basada en posición de cámara
    CP_rot_matrix = np.array([[CP_cos, -CP_sin], [CP_sin, CP_cos]])

    # Matriz de rotación basada en ángulo de posición
    PA_rot_matrix = np.array([[PA_cos, -PA_sin], [PA_sin, PA_cos]])

    # Aplicar rotaciones
    fov_rotated = CP_rot_matrix @ PA_rot_matrix @ [[fov_width], [fov_height]]

    # Desempacar y convertir a escalares
    fov_rot_h = float(fov_rotated[0])
    fov_rot_v = float(fov_rotated[1])

    return fov_rot_h, fov_rot_v


if __name__ == "__main__":
    app.run(debug=True)
