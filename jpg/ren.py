import os
import datetime
import shutil
import sys
import filecmp
import time
import json
from PIL import Image
import piexif
import re

class FileRenamer:
    def __init__(self, dir_out="D:/photos/"):
        self.dir_out = dir_out
        self.formats = [
            "%Y-%m-%d %H.%M.%S.", "%Y-%m-%d_%H.%M.%S_%A.", "%Y-%m-%d_%H.%M.%S_%A_1.",
            "%Y-%m-%d_%H.%M.%S_%A_2.", "%Y-%m-%d_%H.%M.%S_%A_3.", "%Y-%m-%d_%H.%M.%S_%A_4.",
            "%Y-%m-%d_%H.%M.%S_%A_5.", "IMG_%Y%m%d_%H%M%S.", "IMG_%Y%m%d_%H%M%S_1.",
            "IMG_%Y%m%d_%H%M%S_2.", "VID_%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S-ANIMATION."
        ]

    def ren(self, file, ext):
        # Збираємо всі доступні часові мітки
        available_times = []

        # Додаємо час останньої модифікації файлу
        mod_time = self.__get_modification_time(file)
        if mod_time:
            available_times.append(mod_time)
    
        # Додаємо час з JSON файлу, якщо він існує
        json_time = self.__get_creation_time_from_json(file)
        if json_time:
            available_times.append(json_time)
            print(f"Час з JSON файлу для {file}: {json_time}")

        # Додаємо час з імені файлу, якщо він відповідає формату
        for format_str in self.formats:
            name_time = self.__parse_file_date(file, format_str)
            if name_time:
                available_times.append(name_time)

        # Додаємо час з EXIF, якщо він доступний
        try:
            img_file = Image.open(file)
            exif_time = self.__get_minimum_creation_time(img_file._getexif())
            if exif_time:
                img_time = datetime.datetime.strptime(exif_time, "%Y:%m:%d %H:%M:%S")
                available_times.append(img_time)
            img_file.close()
        except (OSError, AttributeError, TypeError, ValueError):
            pass

        # Переконайтеся, що ми маємо хоча б одну часову мітку
        if not available_times:
            raise ValueError("Не знайдено жодної доступної часової мітки для файлу")

        # Знаходимо найраніший час і використовуємо його для перейменування
        new_time = min(available_times)
        self.__rename(new_time, file, ext)

    def __get_modification_time(self, file):
        s = time.ctime(os.path.getmtime(file))
        return datetime.datetime.strptime(s, "%a %b %d %H:%M:%S %Y")

    def __parse_file_date(self, file, format_str):
        try:
            file = file.decode("utf-8")
            return datetime.datetime.strptime(file, format_str)
        except ValueError:
            return None

    def __get_minimum_creation_time(self, exif_data):
        mtime = "9999:99:99 99:99:99"
        if exif_data:
            if 306 in exif_data and exif_data[306] < mtime:  # 306 = DateTime
                mtime = exif_data[306]
            if 36867 in exif_data and exif_data[36867] < mtime:  # DateTimeOriginal
                mtime = exif_data[36867]
            if 36868 in exif_data and exif_data[36868] < mtime:  # DateTimeDigitized
                mtime = exif_data[36868]
        return mtime

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
    
    def __get_creation_time_from_json(self, file):
        # Шукаємо JSON файл з розширенням ".jpg.json"
        json_extension = ".json".encode("utf-8")
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
        except FileNotFoundError:
            # Якщо файл не знайдено, просто пропускаємо цю частину
            pass
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing JSON for file {json_file}: {e}")

        # Якщо файл не існує або є помилка, повертаємо None
        return None


