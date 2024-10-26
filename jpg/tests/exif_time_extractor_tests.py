import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from jpg.exif_time_extractor import ExifTimeExtractor

class TestExifTimeExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = ExifTimeExtractor()

    @patch("jpg.exif_time_extractor.Image.open")
    def test_exif_with_creation_date(self, mock_open):
        # Mock EXIF data with a valid creation date
        mock_image = MagicMock()
        mock_image._getexif.return_value = {
            306: "2023:01:01 12:30:45",
            36867: "2023:01:01 12:30:45",
            36868: "2023:01:01 12:30:45"
        }
        mock_open.return_value = mock_image

        creation_time = self.extractor.get_creation_time("mock_image.jpg")
        self.assertEqual(creation_time, datetime(2023, 1, 1, 12, 30, 45))

    @patch("jpg.exif_time_extractor.Image.open")
    def test_exif_without_creation_date(self, mock_open):
        # Mock EXIF data without a valid creation date
        mock_image = MagicMock()
        mock_image._getexif.return_value = {}
        mock_open.return_value = mock_image

        creation_time = self.extractor.get_creation_time("mock_image.jpg")
        self.assertIsNone(creation_time)

    @patch("jpg.exif_time_extractor.Image.open")
    def test_exif_with_invalid_date_format(self, mock_open):
        # Mock EXIF data with an invalid date format
        mock_image = MagicMock()
        mock_image._getexif.return_value = {
            306: "invalid_date"
        }
        mock_open.return_value = mock_image

        creation_time = self.extractor.get_creation_time("mock_image.jpg")
        self.assertIsNone(creation_time)

    @patch("jpg.exif_time_extractor.Image.open")
    def test_exif_with_partial_dates(self, mock_open):
        # Mock EXIF data with mixed date values
        mock_image = MagicMock()
        mock_image._getexif.return_value = {
            306: "2023:01:01 12:30:45",
            36867: "2024:01:01 12:30:45",
            36868: "2022:01:01 12:30:45"
        }
        mock_open.return_value = mock_image

        creation_time = self.extractor.get_creation_time("mock_image.jpg")
        # Expect the earliest valid date in EXIF data
        self.assertEqual(creation_time, datetime(2022, 1, 1, 12, 30, 45))

    @patch("jpg.exif_time_extractor.Image.open")
    def test_image_open_error(self, mock_open):
        # Simulate an OSError when opening the file
        mock_open.side_effect = OSError("Cannot open file")

        creation_time = self.extractor.get_creation_time("mock_image.jpg")
        self.assertIsNone(creation_time)

if __name__ == "__main__":
    unittest.main()
