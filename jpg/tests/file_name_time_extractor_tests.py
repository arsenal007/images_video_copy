import unittest
from datetime import datetime
from jpg.file_name_time_extractor import FileNameTimeExtractor

class TestFileNameTimeExtractor(unittest.TestCase):
    def setUp(self):
        # Initialize with the requested formats
        self.extractor = FileNameTimeExtractor([
            "%Y-%m-%d %H.%M.%S.", "%Y-%m-%d_%H.%M.%S_%A.", "%Y-%m-%d_%H.%M.%S_%A_1.",
            "%Y-%m-%d_%H.%M.%S_%A_2.", "%Y-%m-%d_%H.%M.%S_%A_3.", "%Y-%m-%d_%H.%M.%S_%A_4.",
            "%Y-%m-%d_%H.%M.%S_%A_5.", "IMG_%Y%m%d_%H%M%S.", "IMG_%Y%m%d_%H%M%S_1.",
            "IMG_%Y%m%d_%H%M%S_2.", "VID_%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S-ANIMATION."
        ])

    def test_format_1(self):
        # Test "%Y-%m-%d %H.%M.%S."
        filename = "2023-10-25 14.30.45."
        expected_date = datetime(2023, 10, 25, 14, 30, 45)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_format_2(self):
        # Test "%Y-%m-%d_%H.%M.%S_%A."
        filename = "2023-10-25_14.30.45_Wednesday."
        expected_date = datetime(2023, 10, 25, 14, 30, 45)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_format_3(self):
        # Test "%Y-%m-%d_%H.%M.%S_%A_1."
        filename = "2023-10-25_14.30.45_Wednesday_1."
        expected_date = datetime(2023, 10, 25, 14, 30, 45)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_format_img(self):
        # Test "IMG_%Y%m%d_%H%M%S."
        filename = "IMG_20231025_143045."
        expected_date = datetime(2023, 10, 25, 14, 30, 45)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_format_vid(self):
        # Test "VID_%Y%m%d_%H%M%S."
        filename = "VID_20231025_143045."
        expected_date = datetime(2023, 10, 25, 14, 30, 45)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_format_animation(self):
        # Test "%Y%m%d_%H%M%S-ANIMATION."
        filename = "20231025_143045-ANIMATION."
        expected_date = datetime(2023, 10, 25, 14, 30, 45)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_invalid_format(self):
        # Test with a filename that does not match any format
        filename = "random_text"
        self.assertIsNone(self.extractor.get_creation_time(filename))

    def test_extra_characters(self):
        # Test with extra characters after the date
        filename = "2023-10-25 14.30.45_extra"
        self.assertIsNone(self.extractor.get_creation_time(filename))

    def test_partial_date(self):
        # Test with a partial date string
        filename = "2023-10-25"
        self.assertIsNone(self.extractor.get_creation_time(filename))

    def test_format_with_invalid_date(self):
        # Test with a valid format structure but invalid date
        filename = "2023-02-30 14.30.45."  # Invalid date
        self.assertIsNone(self.extractor.get_creation_time(filename))

    def test_format_with_timezone(self):
        # Test with a date format that includes timezone (to be ignored)
        filename = "2023-10-25 14.30.45+0200."
        self.assertIsNone(self.extractor.get_creation_time(filename))

    def test_large_date(self):
        # Test with a year beyond realistic scope
        filename = "9999-12-31 23.59.59."
        expected_date = datetime(9999, 12, 31, 23, 59, 59)
        self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

    def test_multiple_formats(self):
        # Test multiple variations of valid formats with day names and suffixes
        filename_variants = [
            ("2023-10-25_14.30.45_Wednesday.", datetime(2023, 10, 25, 14, 30, 45)),
            ("2023-10-25_14.30.45_Wednesday_1.", datetime(2023, 10, 25, 14, 30, 45)),
            ("2023-10-25_14.30.45_Wednesday_2.", datetime(2023, 10, 25, 14, 30, 45)),
            ("IMG_20231025_143045.", datetime(2023, 10, 25, 14, 30, 45)),
            ("VID_20231025_143045.", datetime(2023, 10, 25, 14, 30, 45))
        ]
        for filename, expected_date in filename_variants:
            with self.subTest(filename=filename):
                self.assertEqual(self.extractor.get_creation_time(filename), expected_date)

if __name__ == "__main__":
    unittest.main()
