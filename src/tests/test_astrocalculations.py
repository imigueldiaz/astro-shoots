import unittest
from datetime import datetime
from unittest.mock import patch

from src.app.utils.astro_utils import get_alt_az, get_object_data


class TestAstroCalculations(unittest.TestCase):
    def mock_get_alt_az(self, *args, **kwargs):
        return (None, "Some error message")

    def mock_get_object_data(self, *args, **kwargs):
        return 10.684791666666664, 41.26905555555555, 1, 1, "NGC0224", 0, None

    from datetime import datetime


def test_get_alt_az_with_form_data(self):
    form_data = {
        "object_id": "NGC0224",
        "latitude": 41.075985,
        "longitude": -3.456177,
        "observation_date": datetime(2023, 8, 31, 19, 17, 17, 459910),
    }

    with patch("src.app.utils.astro_utils.get_object_data", self.mock_get_object_data):
        ra, dec, size_major, size_minor, object_name, pa, error = get_object_data(
            form_data["object_id"]
        )

        self.assertEqual(ra, 10.684791666666664)
        self.assertEqual(dec, 41.26905555555555)

        # Convert the datetime object to a UTC time string in 'iso' format
        utc_datetime_str = form_data["observation_date"].strftime("%Y-%m-%dT%H:%M:%S")

        altaz, error_message = get_alt_az(
            ra,
            dec,
            form_data["latitude"],
            form_data["longitude"],
            utc_datetime_str,  # Pass the UTC time string instead of the datetime object
        )

        self.assertIsNotNone(altaz)
        self.assertIsNone(error_message)


if __name__ == "__main__":
    unittest.main()
