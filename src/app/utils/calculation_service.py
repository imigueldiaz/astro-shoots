from astropy.coordinates import EarthLocation
import astropy.units as u
from datetime import datetime


def perform_astro_calculations(
    form_data,
    calculate_camera_fov,
    get_object_data,
    get_alt_az,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    ROUTE,
):
    object_id = form_data["object_id"]
    ra, dec, size_major, size_minor, object_name, pa, error = get_object_data(object_id)

    if error:
        return {"error": error}

    location = EarthLocation(
        lat=form_data["latitude"] * u.deg, lon=form_data["longitude"] * u.deg
    )

    altaz = get_alt_az(location, ra, dec, datetime.utcnow())
    if altaz is None:
        return {
            "error": f"Altitude and azimuth not found for {object_name} ",
        }

    fov_width, fov_height, pixel_width, pixel_height = calculate_camera_fov(
        form_data["sensor_width_mm"],
        form_data["sensor_height_mm"],
        form_data["number_of_pixels_in_width"],
        form_data["number_of_pixels_in_height"],
        form_data["focal_length"],
    )

    max_shooting_time, real_max_shooting_time = calculate_max_shooting_time(
        form_data["aperture"],
        form_data["sensor_width_mm"],
        form_data["number_of_pixels_in_width"],
        form_data["focal_length"],
    )

    (
        num_shoots,
        total_time_minutes,
        total_time_seconds,
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
            "error": f"Object {object_name} number of shoots could be not calculated.",
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
        "route": ROUTE,
        "aperture": form_data["aperture"],
        "focal_length": form_data["focal_length"],
        "total_time_minutes": total_time_minutes,
        "total_time_seconds": total_time_seconds,
        "error": None,
    }

    return result
