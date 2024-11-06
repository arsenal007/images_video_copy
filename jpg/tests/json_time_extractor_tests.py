import unittest
import json
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from jpg.json_time_extractor import JsonTimeExtractor

class TestJsonTimeExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = JsonTimeExtractor()

    @patch("jpg.json_time_extractor.os.path.exists")
    @patch("jpg.json_time_extractor.open", new_callable=mock_open)
    def test_valid_photo_taken_time(self, mock_open, mock_exists):
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        # Sample JSON data with a valid "photoTakenTime" field
        json_data = json.dumps({
            "photoTakenTime": {
                "formatted": "Oct 20, 2023, 05:45:30PM UTC"
            }
        })
        mock_open.return_value.read.return_value = json_data

        # Expected datetime object
        expected_date = datetime(2023, 10, 20, 17, 45, 30)
        self.assertEqual(self.extractor.get_creation_time("test_file"), expected_date)

    @patch("jpg.json_time_extractor.os.path.exists")
    @patch("jpg.json_time_extractor.open", new_callable=mock_open)
    def test_valid_creation_time(self, mock_open, mock_exists):
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        # Sample JSON data with a valid "creationTime" field
        json_data = json.dumps({
            "creationTime": {
                "formatted": "Sep 15, 2023, 08:30:15AM UTC"
            }
        })
        mock_open.return_value.read.return_value = json_data

        # Expected datetime object
        expected_date = datetime(2023, 9, 15, 8, 30, 15)
        self.assertEqual(self.extractor.get_creation_time("test_file"), expected_date)

    @patch("jpg.json_time_extractor.os.path.exists")
    @patch("jpg.json_time_extractor.open", new_callable=mock_open)
    def test_missing_fields(self, mock_open, mock_exists):
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        # JSON data without "photoTakenTime" or "creationTime"
        json_data = json.dumps({})
        mock_open.return_value.read.return_value = json_data

        # Expect None since the required fields are missing
        self.assertIsNone(self.extractor.get_creation_time("test_file"))

    @patch("jpg.json_time_extractor.os.path.exists")
    @patch("jpg.json_time_extractor.open", new_callable=mock_open)
    def test_malformed_json(self, mock_open, mock_exists):
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        # Malformed JSON data
        mock_open.return_value.read.return_value = "{bad json}"

        # Expect None due to JSONDecodeError
        self.assertIsNone(self.extractor.get_creation_time("test_file"))

    @patch("jpg.json_time_extractor.os.path.exists")
    @patch("jpg.json_time_extractor.open", new_callable=mock_open)
    def test_invalid_date_format(self, mock_open, mock_exists):
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        # JSON data with an invalid date format
        json_data = json.dumps({
            "photoTakenTime": {
                "formatted": "Invalid Date Format"
            }
        })
        mock_open.return_value.read.return_value = json_data

        # Expect None due to ValueError on parsing date
        self.assertIsNone(self.extractor.get_creation_time("test_file"))

    @patch("jpg.json_time_extractor.os.path.exists")
    def test_non_existent_file(self, mock_exists):
        # Mock os.path.exists to return False, simulating a missing file
        mock_exists.return_value = False

        # Expect None since the file doesn't exist
        self.assertIsNone(self.extractor.get_creation_time("test_file"))

if __name__ == "__main__":
    unittest.main()
