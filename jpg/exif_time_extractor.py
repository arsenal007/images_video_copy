
import datetime
from PIL import Image

from jpg.creation_time_extractor import CreationTimeExtractor

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