import unittest
from unittest.mock import patch, MagicMock
import os
import json
import datetime
from PIL import Image
import tempfile

# Імпорт класу FileRenamer з нового файлу
from jpg.ren import FileRenamer

class TestRenFunction(unittest.TestCase):
    BASE_DIR = os.path.join("E:", "photos", "jpg_copy", "jpg", "tests", "files")

    @patch("os.path.getmtime")
    @patch("os.rename")
    def test_rename_with_json_date(self, mock_rename, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        
        # Створюємо тимчасовий файл для тесту
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Створюємо JSON файл з даними про дату
        json_file_path = f"{test_file_path}.json"
        json_data = {
            "photoTakenTime": {
                "formatted": "Jan 12, 2020, 4:30:44 PM UTC"
            }
        }
        # Відкриття файлу для запису JSON даних
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file)
        
        # Імітуємо дату останньої модифікації
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Викликаємо функцію
        renamer.ren(test_file_path, "jpg")

        # Перевіряємо, що файл перейменовано з правильною датою з JSON
        expected_new_name = os.path.join(self.BASE_DIR, "2020", "2020-01", "2020-01-12_16.30.44_Sunday.jpg")
        mock_rename.assert_called_with(test_file_path, expected_new_name)

            # Видаляємо тимчасовий файл та JSON файл
        os.unlink(test_file_path)
        os.unlink(json_file_path)


    @patch("os.path.getmtime")
    @patch("PIL.Image.open")
    @patch("os.rename")
    def test_rename_with_exif_date(self, mock_rename, mock_open, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Створюємо тимчасовий файл для тесту
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Імітуємо дату останньої модифікації
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Імітуємо відкриття файлу як зображення та його метадані EXIF
        mock_img = MagicMock()
        mock_img._getexif.return_value = {
            36867: "2023:01:01 10:00:00"  # Дата створення з EXIF
        }
        mock_open.return_value = mock_img

        # Викликаємо функцію
        renamer.ren(test_file_path, "jpg")

        # Перевіряємо, що файл перейменовано з правильною датою
        expected_new_name = os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_10.00.00_Sunday.jpg")
        mock_rename.assert_called_with(test_file_path, expected_new_name)

        # Видаляємо тимчасовий файл
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("os.rename")
    def test_rename_without_exif_date(self, mock_rename, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Створюємо тимчасовий файл для тесту
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Імітуємо дату останньої модифікації
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Викликаємо функцію без EXIF
        with patch("PIL.Image.open", side_effect=OSError):
            renamer.ren(test_file_path, "jpg")

        # Перевіряємо, що файл перейменовано з правильною датою модифікації
        expected_new_name = os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday.jpg")
        mock_rename.assert_called_with(test_file_path, expected_new_name)

        # Видаляємо тимчасовий файл
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("PIL.Image.open")
    @patch("os.rename")
    def test_rename_with_invalid_exif(self, mock_rename, mock_open, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Створюємо тимчасовий файл для тесту
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Імітуємо дату останньої модифікації
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Імітуємо відкриття файлу як зображення з некоректними EXIF даними
        mock_img = MagicMock()
        mock_img._getexif.return_value = {
            36867: "неправильний формат дати"
        }
        mock_open.return_value = mock_img

        # Викликаємо функцію
        renamer.ren(test_file_path, "jpg")

        # Перевіряємо, що файл перейменовано з використанням дати модифікації
        expected_new_name = os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday.jpg")
        mock_rename.assert_called_with(test_file_path, expected_new_name)

        # Видаляємо тимчасовий файл
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("os.rename")
    @patch("os.path.exists")
    @patch("filecmp.cmp", return_value=False)
    def test_rename_with_existing_file(self, mock_cmp, mock_exists, mock_rename, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Створюємо тимчасовий файл для тесту
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Імітуємо дату останньої модифікації
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Імітуємо, що файл з таким ім'ям вже існує
        mock_exists.side_effect = [True, True, False]  # Імітація існуючого файлу двічі, потім неіснуючого

        # Викликаємо функцію
        renamer.ren(test_file_path, "jpg")

        # Оновлений очікуваний результат з індексацією
        expected_new_name = os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday_2.jpg")
        mock_rename.assert_called_with(test_file_path, expected_new_name)

        # Видаляємо тимчасовий файл
        os.unlink(test_file_path)

    @patch("os.path.getmtime")
    @patch("PIL.Image.open")
    @patch("os.rename")
    def test_rename_large_file(self, mock_rename, mock_open, mock_getmtime):
        renamer = FileRenamer(dir_out=self.BASE_DIR)
        # Створюємо тимчасовий файл для тесту
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            test_file_path = temp_file.name

        # Імітуємо дату останньої модифікації
        mock_getmtime.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp()

        # Імітуємо відкриття файлу великого розміру
        mock_img = MagicMock()
        mock_open.return_value = mock_img

        # Викликаємо функцію
        renamer.ren(test_file_path, "mp4")

        # Оновлений очікуваний результат
        expected_new_name = os.path.join(self.BASE_DIR, "2023", "2023-01", "2023-01-01_12.00.00_Sunday.mp4")
        mock_rename.assert_called_with(test_file_path, expected_new_name)

        # Видаляємо тимчасовий файл
        os.unlink(test_file_path)

if __name__ == "__main__":
    unittest.main()
