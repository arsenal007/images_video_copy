import os
import datetime
import shutil
import sys
import filecmp
import time
import json
from PIL import Image
import re

class CreationTimeExtractor:
    def get_creation_time(self, file):
        """
        Повертає час створення файлу або None, якщо час не може бути визначено.
        """
        raise NotImplementedError("Повинно бути реалізовано в підкласі")

class ModificationTimeExtractor(CreationTimeExtractor):
    def get_creation_time(self, file):
        try:
            s = time.ctime(os.path.getmtime(file))
            return datetime.datetime.strptime(s, "%a %b %d %H:%M:%S %Y")
        except Exception as e:
            print(f"Error getting modification time for file {file}: {e}")
            return None

class JsonTimeExtractor(CreationTimeExtractor):
    def get_creation_time(self, file):
        json_extension = ".json"
        json_file = file + json_extension
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if "photoTakenTime" in data and "formatted" in data["photoTakenTime"]:
                        time_str = data["photoTakenTime"]["formatted"]
                        time_str = re.sub(r'[^\x00-\x7F]', '', time_str).strip()
                        return datetime.datetime.strptime(time_str, "%b %d, %Y, %I:%M:%S%p %Z")
                    elif "creationTime" in data and "formatted" in data["creationTime"]:
                        time_str = data["creationTime"]["formatted"]
                        time_str = re.sub(r'[^\x00-\x7F]', '', time_str).strip()
                        return datetime.datetime.strptime(time_str, "%b %d, %Y, %I:%M:%S%p %Z")
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing JSON for file {json_file}: {e}")
        return None

class ExifTimeExtractor(CreationTimeExtractor):
    def get_creation_time(self, file):
        try:
            img_file = Image.open(file)
            exif_data = img_file._getexif()
            if exif_data:
                mtime = "9999:99:99 99:99:99"
                if 306 in exif_data and exif_data[306] < mtime:
                    mtime = exif_data[306]
                if 36867 in exif_data and exif_data[36867] < mtime:
                    mtime = exif_data[36867]
                if 36868 in exif_data and exif_data[36868] < mtime:
                    mtime = exif_data[36868]
                if mtime != "9999:99:99 99:99:99":
                    return datetime.datetime.strptime(mtime, "%Y:%m:%d %H:%M:%S")
            img_file.close()
        except (OSError, AttributeError, TypeError, ValueError) as e:
            print(f"Error extracting EXIF time for file {file}: {e}")
        return None

class FileNameTimeExtractor(CreationTimeExtractor):
    def __init__(self, formats):
        self.formats = formats

    def get_creation_time(self, file):
        for format_str in self.formats:
            try:
                return datetime.datetime.strptime(file, format_str)
            except ValueError:
                continue
        return None

class FileRenamer:
    def __init__(self, dir_out="D:/photos/"):
        self.dir_out = dir_out
        self.formats = [
            "%Y-%m-%d %H.%M.%S.", "%Y-%m-%d_%H.%M.%S_%A.", "%Y-%m-%d_%H.%M.%S_%A_1.",
            "%Y-%m-%d_%H.%M.%S_%A_2.", "%Y-%m-%d_%H.%M.%S_%A_3.", "%Y-%m-%d_%H.%M.%S_%A_4.",
            "%Y-%m-%d_%H.%M.%S_%A_5.", "IMG_%Y%m%d_%H%M%S.", "IMG_%Y%m%d_%H%M%S_1.",
            "IMG_%Y%m%d_%H%M%S_2.", "VID_%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S-ANIMATION."
        ]
        self.extractors = [
            ModificationTimeExtractor(),
            JsonTimeExtractor(),
            ExifTimeExtractor(),
            FileNameTimeExtractor(self.formats)
        ]

    def ren(self, file, ext):
        available_times = []

        # Використовуємо всі екстрактори для отримання часу створення файлу
        for extractor in self.extractors:
            time_value = extractor.get_creation_time(file)
            if time_value:
                available_times.append(time_value)

        # Переконайтеся, що ми маємо хоча б одну часову мітку
        if not available_times:
            raise ValueError("Не знайдено жодної доступної часової мітки для файлу")

        # Знаходимо найраніший час і використовуємо його для перейменування
        new_time = min(available_times)
        self.__rename(new_time, file, ext)

    def __rename(self, new_time, file, ext):
        y = datetime.datetime.strftime(new_time, "%Y")
        m = datetime.datetime.strftime(new_time, "%Y-%m")
        output_dir = os.path.join(self.dir_out, y, m)
        os.makedirs(output_dir, exist_ok=True)
        format_str = "%Y-%m-%d_%H.%M.%S_%A." + ext
        basename = datetime.datetime.strftime(new_time, format_str)
        head, tail = os.path.splitext(basename)
        dst_file = os.path.join(output_dir, basename)

        # Додаємо індексацію, якщо файл вже існує
        count = 0
        while os.path.exists(dst_file) and not filecmp.cmp(file, dst_file):
            count += 1
            dst_file = os.path.join(output_dir, f"{head}_{count}{tail}")

        print(file, dst_file, sep=' -> ', end=']\n', file=sys.stdout, flush=False)
        shutil.move(file, dst_file)