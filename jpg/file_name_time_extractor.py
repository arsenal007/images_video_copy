
import datetime

from jpg.creation_time_extractor import CreationTimeExtractor

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