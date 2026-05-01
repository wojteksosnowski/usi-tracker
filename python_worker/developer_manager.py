import json
import logging
from pathlib import Path
from datetime import datetime
from .csv_importer import slugify

logger = logging.getLogger(__name__)

class DeveloperManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def create_developer_file(self, developer_data: dict):
        """
        Creates or updates a usi_dev_{slug}.json file.
        Expects keys: developer_slug, name, website, portal_mapping.
        """
        dev_slug = developer_data.get("developer_slug")
        if not dev_slug:
            raise ValueError("developer_slug is required")

        dev_dir = self.data_dir / dev_slug
        dev_dir.mkdir(parents=True, exist_ok=True)

        file_path = dev_dir / f"usi_dev_{dev_slug}.json"
        
        # Load existing data to preserve fields or audit info if needed
        existing_data = {}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read existing dev file {file_path}: {e}")

        # Update data
        developer_data["audit"] = existing_data.get("audit", {
            "created_at": datetime.now().isoformat()
        })
        developer_data["audit"]["updated_at"] = datetime.now().isoformat()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(developer_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved developer file: {file_path}")
        return file_path

    def resolve_dev_slug(self, name: str) -> str:
        """Standardizes a developer name into a slug."""
        return slugify(name)
