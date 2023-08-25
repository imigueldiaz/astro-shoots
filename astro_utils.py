import datetime
import json
from astropy.coordinates import AltAz, SkyCoord
import astropy.units as u
from astropy.time import Time
from dsosearcher import DsoSearcher


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


def get_alt_az(location, ra, dec, utc_datetime=None, min_altitude=0, min_speed=0.1):
    """
    Calculate the altitude and azimuth of a celestial object at a given location and time.

    Parameters:
    - location (SkyCoord): The coordinates of the observer's location.
    - ra (float): The right ascension of the celestial object in hour angle.
    - dec (float): The declination of the celestial object in degrees.
    - utc_datetime (datetime, optional): The UTC date and time of observation. If not specified, the current UTC date and time will be used.
    - min_altitude (float, optional): The minimum altitude of the celestial object in degrees. Default is 0.
    - min_speed (float, optional): The minimum speed of change in altitude and azimuth in degrees per minute. Default is 0.1.

    Returns:
    - altaz (AltAz): The altitude and azimuth of the celestial object at the specified time and location.
    """
    if utc_datetime is None:
        utc_datetime = datetime.utcnow()
    obj = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))

    while True:
        altaz = obj.transform_to(AltAz(location=location, obstime=Time(utc_datetime)))
        if (altaz.alt.degree > min_altitude).any():
            next_time = utc_datetime + datetime.timedelta(minutes=1)
            next_altaz = obj.transform_to(
                AltAz(location=location, obstime=Time(next_time))
            )
            avg_altitude_speed = (next_altaz.alt.degree - altaz.alt.degree) * 60
            avg_azimuth_speed = (next_altaz.az.degree - altaz.az.degree) * 60

            if avg_altitude_speed > min_speed and avg_azimuth_speed > min_speed:
                break

        utc_datetime += datetime.timedelta(minutes=1)

    return altaz
