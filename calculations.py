import math

import numpy as np
import astropy.units as u
from astro_utils import get_alt_az


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
):
    """
    Calculate the number of shoots required for a given set of parameters.

    Parameters:
    - altaz: The altaz object representing the current position of the telescope.
    - location: The location of the telescope.
    - ra: The right ascension of the object.
    - dec: The declination of the object.
    - fov_width: The width of the field of view.
    - fov_height: The height of the field of view.
    - size_major: The major size of the object.
    - size_minor: The minor size of the object.
    - exposure_time: The exposure time for each shoot.
    - shoot_interval: The time interval between shoots.
    - camera_position: The position of the camera.
    - PA: The position angle.

    Returns:
    - num_shots: The number of shoots required to cover the object.
    """
    if np.ma.is_masked(size_major) or np.ma.is_masked(size_minor):
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
