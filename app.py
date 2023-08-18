from io import StringIO
from flask import Flask, render_template, redirect, url_for
from flask_limiter import Limiter
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime, timedelta
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u
from astroquery.simbad import Simbad
import numpy as np
import sys
import logging
import configparser
from flask_wtf.csrf import CSRFProtect

# Additional imports for input validation and rate limiting
from wtforms import ValidationError
from flask_talisman import Talisman

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

Simbad.add_votable_fields("dim_majaxis", "dim_minaxis")

# Read the configuration file
config = configparser.ConfigParser()
config.read("config.ini")

# Get the route and static_url_path from the configuration file
route = config.get("APP", "ROUTE")
static_url_path = config.get("APP", "STATIC_URL_PATH")

app = Flask(__name__, static_url_path=static_url_path)

# Set the secret key for your Flask application
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

# Add rate limiting
limiter = Limiter(app, default_limits=["100 per day", "20 per hour"])

csp = {
    "default-src": "'self'",
    "img-src": "*",
    "script-src": "'self'",
    "style-src": "'self' 'unsafe-inline'",
    "font-src": "'self'",
}

talisman = Talisman(app, content_security_policy=csp)
csrf = CSRFProtect(app)


class ObjectForm(FlaskForm):
    object_name = StringField("Object Name", validators=[DataRequired()])
    latitude = FloatField("Latitude", validators=[DataRequired(), NumberRange(-90, 90)])
    longitude = FloatField(
        "Longitude", validators=[DataRequired(), NumberRange(-180, 180)]
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
        "Shoot Interval", validators=[DataRequired(), NumberRange(0, 999)]
    )
    aperture = FloatField("Aperture", validators=[DataRequired(), NumberRange(0, 64)])
    number_of_pixels_in_width = IntegerField(
        "Number of Pixels in Width", validators=[DataRequired(), NumberRange(1, 10000)]
    )
    submit = SubmitField("Submit")


def format_float(value, format_spec=".2f"):
    return format(value, format_spec)


app.jinja_env.filters["format_float"] = format_float


@app.route(f"{route}/", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def index_redirect():
    return redirect(url_for("index"))


@app.route(route, methods=["GET", "POST"])
@limiter.limit("10 per minute")
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

        ra, dec, size_major, size_minor, object_name, error = get_ra_dec_size(
            object_name
        )
        if error:
            return render_template("error.html", error=error)

        location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg)
        altaz = get_alt_az(location, ra, dec, utc_datetime)
        if altaz is None:
            return render_template("error.html", error="Altitude and azimuth not found")

        fov_width, fov_height = calculate_camera_fov(
            sensor_width_mm, sensor_height_mm, focal_length
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
        )

        return render_template(
            "result.html",
            fov_width=fov_width,
            fov_height=fov_height,
            size_major=size_major,
            size_minor=size_minor,
            max_shooting_time=max_shooting_time,
            num_shoots=num_shoots,
            object_name=object_name,
            real_max_shooting_time=real_max_shooting_time,
        )

    return render_template("index.html")


def get_ra_dec_size(object_name):
    result = Simbad.query_object(object_name)
    if result is None:
        return None, None, None, None, None, "Object not found"

    ra = result["RA"][0]
    dec = result["DEC"][0]
    size_major = (
        result["GALDIM_MAJAXIS"][0] if "GALDIM_MAJAXIS" in result.colnames else None
    )
    size_minor = (
        result["GALDIM_MINAXIS"][0] if "GALDIM_MINAXIS" in result.colnames else None
    )

    # Get all identifiers for the object
    identifiers = Simbad.query_objectids(object_name)

    # Find the common name among the identifiers
    common_name = None
    for identifier in identifiers["ID"]:
        id_str = identifier
        if id_str != object_name and "NAME" in id_str:
            common_name = id_str.replace("NAME ", "")
            break

    if common_name:
        object_name = f"{object_name} ({common_name})"
    else:
        object_name = f"{object_name}"

    if size_major is None or size_minor is None:
        # Capture the output of result.pprint()
        output = StringIO()
        sys.stdout = output
        result.pprint()
        sys.stdout = sys.__stdout__

        return (
            None,
            None,
            None,
            None,
            None,
            f"Size data is missing on Simbad for {object_name}\n\n<pre>{output.getvalue()}</pre>",
        )

    return ra, dec, size_major, size_minor, object_name, None


def get_alt_az(location, ra, dec, utc_datetime=None, min_altitude=0, min_speed=0.1):
    if utc_datetime is None:
        utc_datetime = datetime.utcnow()
    obj = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))

    while True:
        altaz = obj.transform_to(AltAz(location=location, obstime=Time(utc_datetime)))
        if altaz.alt.degree > min_altitude:
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


def calculate_camera_fov(sensor_width_mm, sensor_height_mm, focal_length):
    fov_width = (
        2 * (180 / np.pi) * (np.arctan(sensor_width_mm / (2 * focal_length))) * 60
    )
    fov_height = (
        2 * (180 / np.pi) * (np.arctan(sensor_height_mm / (2 * focal_length))) * 60
    )

    return fov_width, fov_height


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
):
    available_altitude = (fov_height - size_major) / 2
    available_azimuth = (fov_width - size_minor) / 2
    current_time = altaz.obstime
    num_shoots = 0
    while True:
        # Calculate the new position of the object after shoot_interval and exposure_time
        next_time = current_time + (shoot_interval + exposure_time) * u.second
        new_altaz = get_alt_az(location, ra, dec, next_time)
        logging.debug(f"AltAz: {new_altaz}")
        avg_altitude_speed = (
            abs(new_altaz.alt.degree - altaz.alt.degree) * 60 / shoot_interval
        )
        avg_azimuth_speed = (
            abs(new_altaz.az.degree - altaz.az.degree) * 60 / shoot_interval
        )
        max_movement_altitude = available_altitude / avg_altitude_speed
        max_movement_azimuth = available_azimuth / avg_azimuth_speed
        total_time_available = (
            min(max_movement_altitude, max_movement_azimuth) * shoot_interval
        )  # Convert minutes to seconds
        total_time_per_shot = exposure_time + shoot_interval
        num_shots = int(total_time_available // total_time_per_shot)
        if num_shots > 0:
            break
        current_time = next_time
        altaz = new_altaz
    return num_shots


if __name__ == "__main__":
    app.run(debug=True)
