from datetime import datetime, date
from typing import Any

import astropy.units as u
from astropy.coordinates import Angle
from astropy.coordinates import EarthLocation
from astropy.time import Time
from dateutil import tz

from app.utils.astro_utils import get_alt_az_at_degrees


def format_altaz_datetime(ra, dec, altaz_obj, observation_datetime) -> str:
    """
    Format the altitude and azimuth of a celestial object along with its right ascension and declination,
    and the observation datetime, into a formatted string.

    Parameters:
        ra (float): The right ascension of the celestial object.
        dec (float): The declination of the celestial object.
        altaz_obj (AltAz): An AltAz object representing the altitude and azimuth of the celestial object.
        observation_datetime (datetime): The datetime of the observation.

    Returns:
        str: A formatted string containing the right ascension, declination, altitude, azimuth, and observation datetime.
    """
    # Convert RA from degrees to hours
    ra_hours = ra / 15

    # Format RA and Dec using the Angle class
    ra_angle = Angle(ra_hours, unit="hourangle")
    dec_angle = Angle(dec, unit="deg")

    # Round the values to 2 decimal places
    alt = round(altaz_obj.alt.degree, 2)
    az = round(altaz_obj.az.degree, 2)

    # Left-fill with zeros to make sure we always get two decimal places
    alt_str = f"{alt:0.2f}"
    az_str = f"{az:0.2f}"

    formatted_datetime = observation_datetime.strftime("%Y-%m-%dT%H:%M") + "Z"

    return f"<span>RA: {ra_angle.to_string(sep=':', pad=True)} Dec: {dec_angle.to_string(sep=':', pad=True, alwayssign=True)} | Alt: {alt_str} Az: {az_str} </span><span> Visible at: {formatted_datetime}</span>"


def perform_astro_calculations(
    form_data,
    calculate_camera_fov,
    get_object_data,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    route,
) -> dict[str, Any]:
    """
    Perform astronomical calculations based on the given form data.

    Args:
        form_data (dict): A dictionary containing the form data.
        calculate_camera_fov (function): A function for calculating the camera field of view.
        get_object_data (function): A function for retrieving object data.
        calculate_max_shooting_time (function): A function for calculating the maximum shooting time.
        calculate_number_of_shoots (function): A function for calculating the number of shoots.
        route (str): The route parameter.

    Returns:
        dict: A dictionary containing the calculated results and other relevant information.
    """
    object_id = form_data["object_id"]
    ra, dec, size_major, size_minor, object_name, pa, error = get_object_data(object_id)

    if error:
        return {"error": error}

    altitude = form_data["altitude"]

    if altitude is not None:
        location = EarthLocation(
            lat=form_data["latitude"] * u.deg,
            lon=form_data["longitude"] * u.deg,
            height=altitude * u.m,
        )
    else:
        location = EarthLocation(
            lat=form_data["latitude"] * u.deg, lon=form_data["longitude"] * u.deg
        )

    # Retrieve observation_date as a datetime.date object
    observation_date = form_data.get("observation_date")
    if observation_date is None:
        return {"error": "Observation date is missing from the form data."}

    # Asegurarse de que observation_date es un objeto datetime.datetime
    if isinstance(observation_date, date) and not isinstance(
        observation_date, datetime
    ):
        observation_datetime = datetime.combine(observation_date, datetime.min.time())
    else:
        observation_datetime = observation_date

    # Establecer la zona horaria del objeto datetime a UTC
    utc_timezone = tz.tzutc()
    observation_datetime_utc = observation_datetime.replace(tzinfo=utc_timezone)

    min_degrees = int(form_data.get("min_degrees", 5))  # Default to 5 if not provided

    # Convertir el objeto datetime.datetime a un objeto Time de Astropy
    observation_time_astropy = Time(observation_datetime_utc)
    # Pass observation_date and min_degrees to get_alt_az
    altaz, error_message, visible_time = get_alt_az_at_degrees(
        location,
        ra,
        dec,
        observation_datetime=observation_time_astropy,
        min_degrees=min_degrees,
    )

    if error_message or altaz is None:
        return {
            "error": error_message
            or f"The object will not be visible as its altitude never reaches {min_degrees} degrees during the observation period."
        }

    fov_width, fov_height, pixel_width, pixel_height = calculate_camera_fov(
        form_data["sensor_width_mm"],
        form_data["sensor_height_mm"],
        form_data["number_of_pixels_in_width"],
        form_data["number_of_pixels_in_height"],
        form_data["focal_length"],
    )

    max_shooting_time, real_max_shooting_time, coc = calculate_max_shooting_time(
        form_data["aperture"],
        form_data["sensor_width_mm"],
        form_data["number_of_pixels_in_width"],
        form_data["focal_length"],
        form_data["sensor_height_mm"],
    )

    (
        num_shoots,
        total_time_minutes,
        total_time_seconds,
        error,
    ) = calculate_number_of_shoots(
        altaz,
        location,
        ra,
        dec,
        fov_width,
        fov_height,
        size_major,
        size_minor,
        max_shooting_time,
        form_data["shoot_interval"],
        form_data["camera_position"],
        pa,
    )

    if num_shoots is None:
        return {
            "error": f"Object {object_name} number of shoots could be not calculated: {error}",
        }

    result = {
        "fov_width": fov_width,
        "fov_height": fov_height,
        "pixel_width": pixel_width,
        "pixel_height": pixel_height,
        "size_major": size_major,
        "size_minor": size_minor,
        "max_shooting_time": max_shooting_time,
        "num_shoots": num_shoots,
        "object_name": object_name,
        "real_max_shooting_time": real_max_shooting_time,
        "pa": pa,
        "camera_position": form_data["camera_position"],
        "route": route,
        "aperture": form_data["aperture"],
        "focal_length": form_data["focal_length"],
        "total_time_minutes": total_time_minutes,
        "total_time_seconds": total_time_seconds,
        "observation_data": format_altaz_datetime(ra, dec, altaz, visible_time),
        "min_degrees": min_degrees,
        "altitude": altitude,
        "error": None,
        "coc": coc,
    }

    return result
