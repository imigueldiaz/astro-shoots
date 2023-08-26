from astropy.coordinates import EarthLocation
import astropy.units as u

from app.utils.astro_utils import find_next_nighttime


def format_altaz_datetime(altaz_obj, observation_datetime):
    """
    Format the given altazimuth datetime.

    Args:
        altaz_obj (AltAz): The altazimuth object to format.
        observation_datetime (datetime): The observation datetime.

    Returns:
        str: The formatted altazimuth datetime string in the format "AR: {ra_str} Dec: {dec_str} | Alt: {alt_str} Az: {az_str} | Visible at: {formatted_datetime}".
    """
    # Round the values to 2 decimal places
    alt = round(altaz_obj.alt.degree, 2)
    az = round(altaz_obj.az.degree, 2)

    # Left-fill with zeros to make sure we always get two decimal places
    alt_str = f"{alt:0.2f}"
    az_str = f"{az:0.2f}"

    # Formatting RA and Dec
    ra = round(altaz_obj.icrs.ra.degree, 2)
    dec = round(altaz_obj.icrs.dec.degree, 2)
    ra_str = f"{ra:0.2f}"
    dec_str = f"{dec:0.2f}"

    formatted_datetime = observation_datetime.strftime("%Y-%m-%dT%H:%M") + "Z"

    return f"AR: {ra_str} Dec: {dec_str} | Alt: {alt_str} Az: {az_str} | Visible at: {formatted_datetime}"


def perform_astro_calculations(
    form_data,
    calculate_camera_fov,
    get_object_data,
    get_alt_az,
    calculate_max_shooting_time,
    calculate_number_of_shoots,
    ROUTE,
):
    """
    Perform astronomical calculations based on the given form data.

    Args:
        form_data (dict): A dictionary containing the form data.
        calculate_camera_fov (function): A function for calculating the camera field of view.
        get_object_data (function): A function for retrieving object data.
        get_alt_az (function): A function for getting the altitude and azimuth.
        calculate_max_shooting_time (function): A function for calculating the maximum shooting time.
        calculate_number_of_shoots (function): A function for calculating the number of shoots.
        ROUTE (str): The route parameter.

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

    # Find the start of the astronomical night
    observation_datetime = find_next_nighttime(location, observation_date, False)

    min_degrees = float(form_data.get("min_degrees", 5))  # Default to 5 if not provided

    # Pass observation_date and min_degrees to get_alt_az
    altaz, error_message = get_alt_az(
        location,
        ra,
        dec,
        observation_datetime=observation_datetime,
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
        form_data["min_degrees"],
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
        "route": ROUTE,
        "aperture": form_data["aperture"],
        "focal_length": form_data["focal_length"],
        "total_time_minutes": total_time_minutes,
        "total_time_seconds": total_time_seconds,
        "observation_data": format_altaz_datetime(altaz, observation_datetime),
        "min_degrees": min_degrees,
        "altitude": altitude,
        "error": None,
    }

    return result
