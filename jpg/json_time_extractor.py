
import os
import json
import datetime
import re 

from jpg.creation_time_extractor import CreationTimeExtractor

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