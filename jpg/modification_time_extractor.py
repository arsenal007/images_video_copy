import datetime
import time
import os

from creation_time_extractor import CreationTimeExtractor

class ModificationTimeExtractor(CreationTimeExtractor):
    def get_creation_time(self, file):
        try:
            s = time.ctime(os.path.getmtime(file))
            return datetime.datetime.strptime(s, "%a %b %d %H:%M:%S %Y")
        except Exception as e:
            print(f"Error getting modification time for file {file}: {e}")
            return None