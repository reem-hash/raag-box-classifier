import os
import json
from datetime import datetime


class Storage:
    def __init__(self):
        # Directory for images
        self.image_dir = "images"
        os.makedirs(self.image_dir, exist_ok=True)

        # Simple JSON DB
        self.db_path = "db.json"
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump([], f)

    def save_image(self, file_bytes: bytes, ext: str):
        """
        Save uploaded image to /images folder
        """
        filename = f"img_{datetime.utcnow().timestamp()}.{ext}"
        filepath = os.path.join(self.image_dir, filename)

        with open(filepath, "wb") as f:
            f.write(file_bytes)

        return filename, filepath

    def log_record(self, record: dict):
        """
        Append a record to db.json
        """
        with open(self.db_path, "r") as f:
            data = json.load(f)

        data.append(record)

        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_all_records(self):
        """
        Return all stored database records
        """
        with open(self.db_path, "r") as f:
            return json.load(f)
