import json
import logging
import re
from pathlib import Path
from datetime import datetime
from .csv_importer import slugify

logger = logging.getLogger(__name__)

class DeveloperManager:
    def __init__(self, data_dir: Path, dev_dir: Path = None):
        self.data_dir = data_dir
        self.dev_dir = dev_dir or (data_dir.parent / "USIdev")
        self.dev_raw_dir = self.dev_dir / "raw"
        self.dev_dir.mkdir(parents=True, exist_ok=True)
        self.dev_raw_dir.mkdir(parents=True, exist_ok=True)
        self.counters_path = Path(__file__).parent / "data" / "usi_counters.json"

    def _get_next_counter(self, key: str) -> int:
        """Atomic-like counter update from file."""
        self.counters_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"dev": 0, "inv": 0}
        if self.counters_path.exists():
            try:
                with open(self.counters_path, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        
        data[key] = data.get(key, 0) + 1
        
        with open(self.counters_path, "w") as f:
            json.dump(data, f, indent=2)
            
        return data[key]

    def generate_usi_id(self, prefix: str) -> str:
        """Generates a new USI ID (e.g., DEV-0001, INV-0001)."""
        key = "dev" if prefix == "DEV" else "inv"
        num = self._get_next_counter(key)
        return f"{prefix}-{num:04d}"

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
            # Skip dev files (legacy location check)
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

    def save_dev_raw_json(self, data: dict, dev_slug: str, portal_prefix: str) -> Path:
        """
        Saves raw developer profile JSON to Public/USIdev/raw/raw_{portal_prefix}_{dev_slug}.json
        with automatic timestamp-based archiving.
        """
        filename = f"raw_{portal_prefix}_{dev_slug}.json"
        file_path = self.dev_raw_dir / filename
        
        if file_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_filename = f"raw_{portal_prefix}_{dev_slug}_{ts}.json"
            archived_path = self.dev_raw_dir / archived_filename
            file_path.rename(archived_path)
            logger.info(f"Archived existing raw developer file: {archived_filename}")
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved raw developer JSON: {file_path}")
        return file_path

    def create_developer_file(self, developer_data: dict):
        """
        Creates or updates a usi_dev_{slug}.json file in self.dev_dir.
        Expects keys: developer_slug, name, website, portal_mapping.
        """
        dev_slug = developer_data.get("developer_slug")
        if not dev_slug:
            raise ValueError("developer_slug is required")

        # Save directly in central USIdev directory
        file_path = self.dev_dir / f"usi_dev_{dev_slug}.json"
        
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
        
        # Ensure usi_dev_id exists
        if "usi_dev_id" not in developer_data:
            if existing_data.get("usi_dev_id"):
                developer_data["usi_dev_id"] = existing_data["usi_dev_id"]
            else:
                developer_data["usi_dev_id"] = self.generate_usi_id("DEV")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(developer_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved developer file: {file_path}")
        return file_path

    def get_developer(self, dev_slug: str) -> dict:
        """Loads developer data from USIdev directory."""
        file_path = self.dev_dir / f"usi_dev_{dev_slug}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading developer file {file_path}: {e}")
            return None

    def list_developers(self) -> list:
        """Returns a list of all developer data objects."""
        developers = []
        for json_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    developers.append(json.load(f))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")
        return developers

    def resolve_dev_slug(self, name: str) -> str:
        """Standardizes a developer name into a slug."""
        return slugify(name)

    def merge_developers(self, target_slug: str, source_slug: str) -> bool:
        """
        Merges source developer into target developer.
        Moves all investment folders and updates USI JSONs.
        """
        target_dev = self.get_developer(target_slug)
        source_dev = self.get_developer(source_slug)
        
        if not target_dev or not source_dev:
            logger.error(f"Merge failed: target {target_slug} or source {source_slug} not found.")
            return False
            
        source_data_dir = self.data_dir / source_slug
        target_data_dir = self.data_dir / target_slug
        
        if source_data_dir.exists():
            target_data_dir.mkdir(parents=True, exist_ok=True)
            for inv_dir in source_data_dir.iterdir():
                if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                    inv_slug = inv_dir.name
                    target_inv_dir = target_data_dir / inv_slug
                    
                    # Handle name collision
                    if target_inv_dir.exists():
                        ts = datetime.now().strftime("%Y%m%d")
                        target_inv_dir = target_data_dir / f"{inv_slug}_{ts}"
                    
                    # Move folder
                    inv_dir.rename(target_inv_dir)
                    
                    # Update USI JSON inside
                    usi_file = target_inv_dir / f"usi_{inv_slug}.json"
                    if usi_file.exists():
                        try:
                            with open(usi_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            data["developer_slug"] = target_slug
                            data["usi_dev_id"] = target_dev["usi_dev_id"]
                            data["developer"] = target_dev["name"]
                            with open(usi_file, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                        except Exception as e:
                            logger.error(f"Error updating USI file during merge: {e}")

            # Remove empty source dir
            try:
                if not any(source_data_dir.iterdir()):
                    source_data_dir.rmdir()
            except Exception:
                pass
                
        # Archive source developer JSON
        source_file = self.dev_dir / f"usi_dev_{source_slug}.json"
        archive_dir = self.dev_dir / "archived"
        archive_dir.mkdir(parents=True, exist_ok=True)
        source_file.rename(archive_dir / f"usi_dev_{source_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Merge portal mappings to target (optional, but good practice)
        # ... logic to merge mappings if target has nulls ...
        
        logger.info(f"Successfully merged {source_slug} into {target_slug}")
        return True

    def dismiss_suggestion(self, dev_slug: str, suggested_id: str) -> bool:
        """Removes a suggestion from developer record."""
        dev = self.get_developer(dev_slug)
        if not dev or "suggestions" not in dev:
            return False
            
        new_suggestions = [s for s in dev["suggestions"] if s["usi_dev_id"] != suggested_id]
        if len(new_suggestions) == len(dev["suggestions"]):
            return False
            
        dev["suggestions"] = new_suggestions
        self.create_developer_file(dev)
        return True
