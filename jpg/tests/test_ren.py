import unittest
from unittest.mock import patch, MagicMock
import os
import json
import datetime
from PIL import Image
import tempfile

# Import FileRenamer class
from jpg.ren import FileRenamer

class TestRenFunction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.BASE_DIR = tempfile.mkdtemp(prefix="test_ren_")

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.BASE_DIR, ignore_errors=True)

    @patch("os.path.getmtime")
    @patch("shutil.move")
    def test_rename_with_json_date(self, mock_move, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)

        # Creating a temporary file for the test
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Create JSON file with date data (format without space before AM/PM)
        json_file_path = f"{test_file_path}.json"
        json_data = {
            "photoTakenTime": {
                "formatted": "Jan 12, 2020, 4:30:44PM UTC"
            }
        }
        # Open file and write JSON data
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file)

        # Mock file modification date
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Call the function
        renamer.ren(test_file_path, "jpg")

        # Verify file was renamed with correct date from JSON (bytes path)
        expected_new_name = os.fsencode(os.path.join(self.BASE_DIR, "2020", "2020-01", "2020-01-12_16.30.44_Sunday.jpg"))
        mock_move.assert_called_with(test_file_path, expected_new_name)

        # Delete temporary file (JSON already deleted by extractor)
        os.unlink(test_file_path)


    @patch("os.path.getmtime")
    @patch("PIL.Image.open")
    @patch("shutil.move")
    def test_rename_with_exif_date(self, mock_move, mock_open, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Create temporary file for test
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Mock file modification date
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Mock opening file as image and its EXIF metadata
        mock_img = MagicMock()
        mock_img._getexif.return_value = {
            36867: "2023:01:01 10:00:00"  # Creation date from EXIF
        }
        mock_open.return_value = mock_img

        # Call the function
        renamer.ren(test_file_path, "jpg")

        # Verify file was renamed with correct date (bytes path)
        expected_new_name = os.fsencode(os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_10.00.00_Sunday.jpg"))
        mock_move.assert_called_with(test_file_path, expected_new_name)

        # Delete temporary file
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("shutil.move")
    def test_rename_without_exif_date(self, mock_move, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Create temporary file for test
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Mock file modification date
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Call function without EXIF
        with patch("PIL.Image.open", side_effect=OSError):
            renamer.ren(test_file_path, "jpg")

        # Verify file was renamed with correct modification date (bytes path)
        expected_new_name = os.fsencode(os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday.jpg"))
        mock_move.assert_called_with(test_file_path, expected_new_name)

        # Delete temporary file
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("PIL.Image.open")
    @patch("shutil.move")
    def test_rename_with_invalid_exif(self, mock_move, mock_open, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Create temporary file for test
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Mock file modification date
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Mock opening file as image with invalid EXIF data
        mock_img = MagicMock()
        mock_img._getexif.return_value = {
            36867: "invalid date format"
        }
        mock_open.return_value = mock_img

        # Call the function
        renamer.ren(test_file_path, "jpg")

        # Verify file was renamed using modification date (bytes path)
        expected_new_name = os.fsencode(os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday.jpg"))
        mock_move.assert_called_with(test_file_path, expected_new_name)

        # Delete temporary file
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("jpg.ren.shutil.move")
    @patch("jpg.ren.os.makedirs")
    @patch("jpg.ren.filecmp.cmp", return_value=False)
    @patch("jpg.ren.os.path.exists")
    def test_rename_with_existing_file(self, mock_exists, mock_cmp, mock_makedirs, mock_move, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Create temporary file for test
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Mock file modification date
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Function to mock exists() - returns True for files without suffix and _1, False for _2
        def exists_side_effect(path):
            path_str = os.fsdecode(path) if isinstance(path, bytes) else path
            if "_2.jpg" in path_str:
                return False
            if "_1.jpg" in path_str:
                return True
            if "Sunday.jpg" in path_str:
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        # Call the function
        renamer.ren(test_file_path, "jpg")

        # Expected result with indexing (bytes path)
        expected_new_name = os.fsencode(os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday_2.jpg"))
        mock_move.assert_called_with(test_file_path, expected_new_name)

        # Delete temporary file
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("PIL.Image.open")
    @patch("shutil.move")
    def test_rename_large_file(self, mock_move, mock_open, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Create temporary file for test
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Mock file modification date
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Mock opening large file
        mock_img = MagicMock()
        mock_open.return_value = mock_img

        # Call the function
        renamer.ren(test_file_path, "mp4")

        # Expected result (bytes path)
        expected_new_name = os.fsencode(os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday.mp4"))
        mock_move.assert_called_with(test_file_path, expected_new_name)

        # Delete temporary file
        os.unlink(test_file_path)

if __name__ == "__main__":
    unittest.main()
