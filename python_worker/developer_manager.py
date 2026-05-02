import json
import logging
import re
from pathlib import Path
from datetime import datetime
from .csv_importer import slugify

logger = logging.getLogger(__name__)

class DeveloperManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def get_existing_identifiers(self) -> dict:
        """
        Scans USI_DATA_DIR for existing investments and returns a dict with sets of IDs.
        """
        rp_ids = set()
        oto_ids = set()
        oto_slugs = set()
        to_ids = set()

        logger.info(f"Scanning {self.data_dir} for existing identifiers...")
        
        # Using rglob to find all usi_*.json files in subdirectories
        for json_file in self.data_dir.rglob("usi_*.json"):
            # Skip dev files
            if json_file.name.startswith("usi_dev_"):
                continue
            
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                sources = data.get("sources", {})
                
                # RP
                rp_src = sources.get("rp", {})
                if rp_src and rp_src.get("id"):
                    rp_ids.add(str(rp_src["id"]))
                
                # Otodom
                oto_src = sources.get("oto", {})
                if oto_src:
                    if oto_src.get("id"):
                        oto_ids.add(str(oto_src["id"]))
                    
                    url = oto_src.get("url")
                    if url:
                        # Extract slug: /inwestycja/SLUG or /oferta/SLUG
                        match = re.search(r"/(?:inwestycja|oferta)/([^/?#]+)", url)
                        if match:
                            oto_slugs.add(match.group(1))

                # TabelaOfert
                to_src = sources.get("to", {})
                if to_src and to_src.get("id"):
                    to_ids.add(str(to_src["id"]))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        logger.info(f"Found {len(rp_ids)} RP IDs, {len(oto_ids)} Otodom IDs, and {len(to_ids)} TO IDs.")
        return {
            "rp_ids": rp_ids,
            "oto_ids": oto_ids,
            "oto_slugs": oto_slugs,
            "to_ids": to_ids
        }

    def save_raw_json(self, data: dict, dev_slug: str, inv_slug: str, portal_prefix: str) -> Path:
        """
        Saves raw JSON data to Public/USIdata/{dev_slug}/{inv_slug}/raw_{portal_prefix}_{inv_slug}.json
        with automatic timestamp-based archiving of existing files.
        """
        inv_dir = self.data_dir / dev_slug / inv_slug
        inv_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"raw_{portal_prefix}_{inv_slug}.json"
        file_path = inv_dir / filename
        
        if file_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_filename = f"raw_{portal_prefix}_{inv_slug}_{ts}.json"
            archived_path = inv_dir / archived_filename
            file_path.rename(archived_path)
            logger.info(f"Archived existing raw file: {archived_filename}")
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved raw JSON: {file_path}")
        return file_path

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
