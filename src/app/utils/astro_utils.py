import json
from astropy.coordinates import AltAz, SkyCoord
import astropy.units as u
from astropy.time import Time, TimeDelta
from app.search.dsosearcher import DsoSearcher
from astral import LocationInfo
import astral.sun

from datetime import datetime, timedelta, timezone


def find_next_nighttime(location, observation_date, dawnTime=True):
    latitude, longitude = location.lat.deg, location.lon.deg
    l = LocationInfo("name", "region", "timezone/name", latitude, longitude)
    night_time, dawn_time = astral.sun.night(l.observer, date=observation_date)

    # Extract the time components from the Time object
    if dawnTime:
        selected_time = dawn_time.time()
    else:
        selected_time = night_time.time()

    # Combine the observation_date (a date object) with the time components
    combined_datetime = datetime.combine(observation_date, selected_time)

    return combined_datetime  # This will return the combined datetime object


def count_dso():
    return DsoSearcher.count_objects()


def get_object_data(object_id):
    """
    Retrieves data for a given object ID.

    Parameters:
    - object_id (str): The ID of the object.

    Returns:
    - ra (float): The right ascension of the object in degrees.
    - dec (float): The declination of the object in degrees.
    - size_major (float): The major axis size of the object.
    - size_minor (float): The minor axis size of the object.
    - object_id (str): The ID of the object.
    - pa (float): The position angle of the object.
    - error_message (str): An error message if the object ID is not found or if size data is missing.
    """
    result_json = DsoSearcher.get(object_id)

    if result_json is None:
        return None, None, None, None, None, None, f"Object {object_id} not found"

    # Parsing the JSON string into a dictionary
    result = json.loads(result_json)

    ra_hms = result["coordinates"]["right ascension"]
    dec_dms = result["coordinates"]["declination"]

    # Create a SkyCoord object using the HMS and DMS values
    coord = SkyCoord(ra=ra_hms, dec=dec_dms, unit=(u.hourangle, u.deg))

    ra = coord.ra.deg
    dec = coord.dec.deg

    # Find the common name among the identifiers
    other_identifiers = result.get("other identifiers", {})
    common_names = other_identifiers.get("common names", [result["type"]])
    common_name = common_names[0] if common_names else result["type"]

    object_name = f"{result['name']} ({common_name})"

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

    return ra, dec, size_major, size_minor, object_name, pa, None


def get_alt_az(location, ra, dec, observation_datetime=None, min_degrees=5):
    print(f"RA: {ra}, Dec: {dec}")

    if observation_datetime is None:
        observation_datetime = datetime.utcnow().replace(tzinfo=timezone.utc)

    # Convert datetime to Time object if needed
    if not isinstance(observation_datetime, Time):
        observation_datetime = Time(observation_datetime)

    obj = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))
    current_time = observation_datetime

    # Add one day to the current time
    next_day_time = current_time + TimeDelta(1 * 24 * 60 * 60, format="sec")

    # Find the astronomical dawn of the next day
    next_day_dawn = find_next_nighttime(location, next_day_time.datetime.date(), True)
    limit_time = Time(next_day_dawn)

    while True:
        print(f"Current Time: {current_time}, Limit Time: {limit_time}")

        altaz = obj.transform_to(AltAz(location=location, obstime=current_time))
        if altaz.alt.degree >= min_degrees or current_time >= limit_time:
            break
        current_time += TimeDelta(60, format="sec")  # Adds one minute
    if altaz.alt.degree < min_degrees:
        return (
            None,
            f"The object will not be visible as its altitude never reaches {min_degrees} degrees during the observation period.",
        )

    return altaz, None
