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
        Append a record to db.json with timestamp
        """
        # Add timestamp if not present
        if "timestamp" not in record:
            record["timestamp"] = datetime.utcnow().isoformat()
        
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
    
    def get_driver_records(self, driver_id: str):
        """
        Get all records for a specific driver
        """
        all_records = self.get_all_records()
        return [r for r in all_records if r.get("driver_id") == driver_id]
    
    def get_driver_statistics(self, driver_id: str):
        """
        Calculate statistics for a specific driver
        """
        records = self.get_driver_records(driver_id)
        
        if not records:
            return {
                "total_evaluations": 0,
                "ok_count": 0,
                "needs_fix_count": 0,
                "average_confidence": 0.0,
                "feedback_count": 0
            }
        
        ok_count = len([r for r in records if r.get("condition") == "OK"])
        needs_fix_count = len([r for r in records if r.get("condition") == "NEEDS_FIX"])
        feedback_count = len([r for r in records if r.get("feedback", False)])
        
        confidences = [r.get("confidence", 0) for r in records if "confidence" in r]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_evaluations": len(records),
            "ok_count": ok_count,
            "needs_fix_count": needs_fix_count,
            "average_confidence": avg_confidence,
            "feedback_count": feedback_count,
            "damage_rate": needs_fix_count / len(records) if records else 0.0
        }
