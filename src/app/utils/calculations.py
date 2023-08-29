import math

import astropy.units as u
import numpy as np
from astropy.time import TimeDelta

from .astro_utils import get_alt_az


def calculate_camera_fov(
    sensor_width_mm,
    sensor_height_mm,
    horizontal_pixels,
    vertical_pixels,
    focal_length_mm,
):
    """
    Calculate the field of view (FOV) of a camera based on the sensor dimensions, pixel dimensions, and focal length.

    Parameters:
        sensor_width_mm (float): The width of the camera sensor in millimeters.
        sensor_height_mm (float): The height of the camera sensor in millimeters.
        horizontal_pixels (int): The number of pixels in the horizontal direction.
        vertical_pixels (int): The number of pixels in the vertical direction.
        focal_length_mm (float): The focal length of the camera lens in millimeters.

    Returns:
        fov_horizontal_arcminutes (float): The horizontal field of view in arcminutes.
        fov_vertical_arcminutes (float): The vertical field of view in arcminutes.
        pixel_width_arcsec (float): The width of each pixel in arcseconds.
        pixel_height_arcsec (float): The height of each pixel in arcseconds.
    """
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


def calculate_max_shooting_time(
    aperture, sensor_width_mm, number_of_pixels_in_width, focal_length
):
    """
    Calculate the maximum shooting time based on the given aperture, sensor width, number of pixels in width, and focal length.

    Parameters:
        aperture (float): The aperture value.
        sensor_width_mm (float): The width of the camera sensor in millimeters.
        number_of_pixels_in_width (int): The number of pixels in the width of the camera sensor.
        focal_length (float): The focal length of the camera lens.

    Returns:
        tuple: A tuple containing the rounded shutter speed and the original shutter speed in seconds.
    """
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
    min_degrees,
):
    """
    Calculate the number of shoots required for a given set of parameters.
    """

    # Ensure the time is in UTC
    if altaz.obstime.scale != "utc":
        raise ValueError("Time scale should be UTC.")

    if np.ma.is_masked(size_major) or np.ma.is_masked(size_minor):
        return None, 0, 0, "Size data is missing (masked)."

    # Applying rotation to FOV
    fov_rot_h, fov_rot_v = apply_fov_rotation(
        fov_width, fov_height, camera_position, PA
    )

    available_altitude = abs(fov_rot_h - size_major) / 2
    available_azimuth = abs(fov_rot_v - size_minor) / 2
    current_time = altaz.obstime
    num_shoots = 0

    while True:
        # Ensure the time is in UTC
        if current_time.scale != "utc":
            raise ValueError("Time scale should be UTC.")

        # Calculate the new position of the object after shoot_interval and exposure_time
        next_time = current_time + TimeDelta(
            (shoot_interval + exposure_time) * u.second
        )

        new_altaz, error = get_alt_az(
            location,
            ra,
            dec,
            next_time,
        )

        if new_altaz is None:
            return (None, 0, 0, error)

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
        )

        total_time_per_shot = exposure_time + shoot_interval
        num_shoots = max(0, total_time_available // total_time_per_shot)

        if num_shoots > 0:
            break

        current_time = next_time
        altaz = new_altaz

    total_time_seconds = num_shoots * (exposure_time + shoot_interval)

    # Convert the total time to minutes and seconds
    total_time_minutes = int(round(total_time_seconds // 60))
    total_time_seconds = int(round(total_time_seconds % 60))

    return int(num_shoots), total_time_minutes, total_time_seconds, None


def apply_fov_rotation(fov_width, fov_height, camera_position, PA):
    """
    Apply field of view (FOV) rotation to the given FOV width, FOV height, camera position, and PA.

    Parameters:
        - fov_width (float): The width of the field of view.
        - fov_height (float): The height of the field of view.
        - camera_position (int): The position of the camera.
        - PA (float): The PA value.

    Returns:
        - fov_rot_h (float): The rotated width of the field of view.
        - fov_rot_v (float): The rotated height of the field of view.
    """
    if camera_position in [0, 90, -90]:
        fov_rot_h = fov_width if camera_position == 0 else fov_height
        fov_rot_v = fov_height if camera_position == 0 else fov_width
    else:
        fov_rot_h, fov_rot_v = rotate_fov(fov_width, fov_height, camera_position, PA)
    return fov_rot_h, fov_rot_v


def rotate_fov(fov_width, fov_height, camera_position, PA):
    """
    Rotate the field of view (FOV) dimensions based on the camera position and the position angle (PA).

    Args:
        fov_width (float): The width of the field of view.
        fov_height (float): The height of the field of view.
        camera_position (float): The position of the camera in degrees.
        PA (float): The position angle in degrees.

    Returns:
        tuple: A tuple containing the rotated FOV dimensions (fov_rot_h, fov_rot_v).

    """
    # Convertir ángulos a radianes
    PA_rad = PA * np.pi / 180

    camera_rot_rad = camera_position * np.pi / 180

    # Calcular componentes de rotación
    CP_sin = np.sin(camera_rot_rad)
    CP_cos = np.cos(camera_rot_rad)

    PA_sin = np.sin(PA_rad)
    PA_cos = np.cos(PA_rad)
    # rotation matrix based on camera position
    CP_rot_matrix = np.array([[CP_cos, -CP_sin], [CP_sin, CP_cos]])

    # rotation matrix based on PA
    PA_rot_matrix = np.array([[PA_cos, -PA_sin], [PA_sin, PA_cos]])

    # Apply rotation
    fov_rotated = CP_rot_matrix @ PA_rot_matrix @ [[fov_width], [fov_height]]

    # unpack and convert to float
    fov_rot_h = float(fov_rotated[0])
    fov_rot_v = float(fov_rotated[1])

    return fov_rot_h, fov_rot_v


def round_down_shutter_speed(shutter_speed):
    """
    Rounds down a given shutter speed to the nearest standard shutter speed value.

    Parameters:
    - shutter_speed (float): The original shutter speed value to be rounded down.

    Returns:
    - rounded_shutter_speed (float): The nearest standard shutter speed value that is less than or equal to the original shutter speed.
    """
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
