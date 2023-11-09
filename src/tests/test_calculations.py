import unittest
import numpy as np
from astropy.time import Time
from astropy.coordinates import AltAz
from src.app.utils.calculations import calculate_camera_fov, calculate_number_of_shoots


class TestCalculations(unittest.TestCase):
    def test_calculate_number_of_shoots_masked_size(self):
        altaz = AltAz(obstime=Time("2022-01-01 00:00:00", scale="utc"))
        size_major = np.ma.masked
        size_minor = 1
        result = calculate_number_of_shoots(
            altaz,
            None,
            None,
            None,
            None,
            None,
            size_major,
            size_minor,
            None,
            None,
            None,
            None,
        )
        self.assertEqual(result, (None, 0, 0, "Size data is missing (masked)."))

    def test_calculate_number_of_shoots_non_utc_time(self):
        altaz = AltAz(obstime=Time("2022-01-01 00:00:00", scale="tai"))
        size_major = 1
        size_minor = 1
        with self.assertRaises(ValueError) as context:
            calculate_number_of_shoots(
                altaz,
                None,
                None,
                None,
                None,
                None,
                size_major,
                size_minor,
                None,
                None,
                None,
                None,
            )
        self.assertTrue("Time scale should be UTC." in str(context.exception))

    def test_calculate_camera_fov(self):
        sensor_width_mm = 36.0
        sensor_height_mm = 24.0
        horizontal_pixels = 6000
        vertical_pixels = 4000
        focal_length_mm = 50.0

        (
            fov_horizontal_arcminutes,
            fov_vertical_arcminutes,
            pixel_width_arcmin,
            pixel_height_arcmin,
        ) = calculate_camera_fov(
            sensor_width_mm,
            sensor_height_mm,
            horizontal_pixels,
            vertical_pixels,
            focal_length_mm,
        )

        self.assertAlmostEqual(fov_horizontal_arcminutes, 39.6 * 60, delta=3)
        self.assertAlmostEqual(fov_vertical_arcminutes, 27.0 * 60, delta=3)
        self.assertAlmostEqual(pixel_width_arcmin, 0.4 * 60, delta=3)
        self.assertAlmostEqual(pixel_height_arcmin, 0.4 * 60, delta=3)

    def test_calculate_camera_fov_with_different_focal_length(self):
        sensor_width_mm = 36.0
        sensor_height_mm = 24.0
        horizontal_pixels = 6000
        vertical_pixels = 4000
        focal_length_mm = 35.0

        (
            fov_horizontal_arcminutes,
            fov_vertical_arcminutes,
            pixel_width_arcmin,
            pixel_height_arcmin,
        ) = calculate_camera_fov(
            sensor_width_mm,
            sensor_height_mm,
            horizontal_pixels,
            vertical_pixels,
            focal_length_mm,
        )

        self.assertAlmostEqual(fov_horizontal_arcminutes, 54.4 * 60, delta=3)
        self.assertAlmostEqual(fov_vertical_arcminutes, 37.8 * 60, delta=3)
        self.assertAlmostEqual(pixel_width_arcmin, 0.5 * 60, delta=3)
        self.assertAlmostEqual(pixel_height_arcmin, 0.6 * 60, delta=3)


if __name__ == "__main__":
    unittest.main()
