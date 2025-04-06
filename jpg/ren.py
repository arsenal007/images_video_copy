import os
import datetime
import shutil
import sys
import filecmp

from jpg.modification_time_extractor import ModificationTimeExtractor
from jpg.json_time_extractor import JsonTimeExtractor
from jpg.exif_time_extractor import ExifTimeExtractor
from jpg.file_name_time_extractor import FileNameTimeExtractor

class FileRenamer:
    def __init__(self, dir_out="D:/photos/"):
        self.dir_out = os.fsencode(dir_out)  # Конвертуємо dir_out у bytes для послідовності
        self.formats = [ "%Y-%m-%d %H.%M.%S.", "%Y-%m-%d_%H.%M.%S_%A.", "%Y-%m-%d_%H.%M.%S_%A_1.",
            "%Y-%m-%d_%H.%M.%S_%A_2.", "%Y-%m-%d_%H.%M.%S_%A_3.", "%Y-%m-%d_%H.%M.%S_%A_4.",
            "%Y-%m-%d_%H.%M.%S_%A_5.", "IMG_%Y%m%d_%H%M%S.", "IMG_%Y%m%d_%H%M%S_1.",
            "IMG_%Y%m%d_%H%M%S_2.", "VID_%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S.", "%Y%m%d_%H%M%S-ANIMATION.",
            "%Y%m%d_%H%M%S"
        ]

        self.extractors = [
            ModificationTimeExtractor(),
            JsonTimeExtractor(),
            ExifTimeExtractor(),
            FileNameTimeExtractor(self.formats)
        ]

    def ren(self, file, ext):
        # Декодуємо назву файлу перед передачею в екстрактори
        file_str = os.fsdecode(file) if isinstance(file, bytes) else file
        available_times = []

        # Використовуємо всі екстрактори для отримання часу створення файлу
        for extractor in self.extractors:
            time_value = extractor.get_creation_time(file_str)
            if time_value:
                available_times.append(time_value)

        # Переконайтеся, що ми маємо хоча б одну часову мітку
        if not available_times:
            raise ValueError("Не знайдено жодної доступної часової мітки для файлу")

        # Знаходимо найраніший час і використовуємо його для перейменування
        new_time = min(available_times)
        self.__rename(new_time, file, ext)  # Передаємо оригінальний байтовий шлях

    def __rename(self, new_time, file, ext):
        y = datetime.datetime.strftime(new_time, "%Y")
        m = datetime.datetime.strftime(new_time, "%Y-%m")
        output_dir = os.path.join(self.dir_out, os.fsencode(y), os.fsencode(m))
        os.makedirs(output_dir, exist_ok=True)
        
        format_str = "%Y-%m-%d_%H.%M.%S_%A." + ext
        basename = datetime.datetime.strftime(new_time, format_str)
        head, tail = os.path.splitext(basename)
        dst_file = os.path.join(output_dir, os.fsencode(basename))

        # Додаємо індексацію, якщо файл вже існує
        count = 0
        while os.path.exists(dst_file) and not filecmp.cmp(file, dst_file):
            count += 1
            indexed_basename = f"{head}_{count}{tail}"
            dst_file = os.path.join(output_dir, os.fsencode(indexed_basename))

        print(os.fsdecode(file), os.fsdecode(dst_file), sep=' -> ', end=']\n', file=sys.stdout, flush=False)
        shutil.move(file, dst_file)
