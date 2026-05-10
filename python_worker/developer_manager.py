import json
import logging
import re
import shutil
from pathlib import Path
from datetime import datetime
from .csv_importer import slugify

logger = logging.getLogger(__name__)

class DeveloperManager:
    def __init__(self, data_dir: Path, dev_dir: Path = None):
        self.data_dir = data_dir
        self.dev_dir = dev_dir or (data_dir.parent / "USIdev")
        self.dev_raw_dir = self.dev_dir / "raw"
        try:
            self.dev_dir.mkdir(parents=True, exist_ok=True)
            self.dev_raw_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Note: Could not verify/create directories {self.dev_dir} or {self.dev_raw_dir} due to OS permissions. Proceeding anyway. Error: {e}")
        self.counters_path = Path(__file__).parent / "data" / "usi_counters.json"
        
        # Initialize library-based technical manager
        from python_worker.config import get_scraper_config
        from usi_scrapers.manager import TechnicalDataManager
        config = get_scraper_config()
        self.tech_manager = TechnicalDataManager(config) if config else None

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
        Includes a 5-minute cache to speed up repeated UI calls.
        """
        now = datetime.now()
        if hasattr(self, "_identifiers_cache"):
            cache_time, cache_data = self._identifiers_cache
            if (now - cache_time).total_seconds() < 300:
                logger.info("Using cached identifiers (valid for 5m)")
                return cache_data

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
                # OPTIMIZATION: Read first 4KB to check if it has sources before full parse
                # (actually for small USI files, just reading is fine)
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                sources = data.get("sources", {})
                if not sources: continue
                
                # RP
                rp_src = sources.get("rp", {})
                if rp_src and rp_src.get("id"):
                    val = str(rp_src["id"])
                    if val and val != "None":
                        rp_ids.add(val)
                
                # Otodom
                oto_src = sources.get("oto", {})
                if oto_src:
                    if oto_src.get("id"):
                        val = str(oto_src["id"])
                        if val and val != "None":
                            oto_ids.add(val)
                    
                    url = oto_src.get("url")
                    if url:
                        # Extract full slug: /inwestycja/SLUG or /oferta/SLUG
                        match = re.search(r"/(?:inwestycja|oferta)/([^/?#]+)", url)
                        if match:
                            full_slug = match.group(1)
                            oto_slugs.add(full_slug)
                            # Also extract Hash ID (part after -ID) as per Coda spec
                            hash_match = re.search(r"-ID([a-zA-Z0-9]+)$", full_slug)
                            if hash_match:
                                oto_ids.add(hash_match.group(1))
                            elif "-ID" not in full_slug and len(full_slug) > 5:
                                coda_hash_match = re.search(r"ID([a-zA-Z0-9]+)$", full_slug)
                                if coda_hash_match:
                                    oto_ids.add(coda_hash_match.group(1))

                # TabelaOfert
                to_src = sources.get("to", {})
                if to_src and to_src.get("id"):
                    val = str(to_src["id"])
                    if val and val != "None":
                        to_ids.add(val)
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        logger.info(f"Found {len(rp_ids)} RP IDs, {len(oto_ids)} Otodom IDs, and {len(to_ids)} TO IDs.")
        result = {
            "rp_ids": rp_ids,
            "oto_ids": oto_ids,
            "oto_slugs": oto_slugs,
            "to_ids": to_ids
        }
        self._identifiers_cache = (now, result)
        return result

    def save_raw_json(self, data: dict, dev_slug: str, inv_slug: str, portal_prefix: str) -> Path:
        """Delegates raw investment JSON saving to the library manager."""
        if self.tech_manager:
            from usi_scrapers import api as scraper_api
            return scraper_api.save_raw(self.tech_manager.config, data, dev_slug, inv_slug, portal_prefix)

        # Fallback (legacy)
        inv_dir = self.data_dir / dev_slug / inv_slug
        inv_dir.mkdir(parents=True, exist_ok=True)
        filename = f"raw_{portal_prefix}_{inv_slug}.json"
        file_path = inv_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    def save_dev_raw_json(self, data: dict, dev_slug: str, portal_prefix: str) -> Path:
        """Delegates raw developer JSON saving to the library manager."""
        if self.tech_manager:
            from usi_scrapers import api as scraper_api
            return scraper_api.save_raw_developer(self.tech_manager.config, data, dev_slug, portal_prefix)

        # Fallback (legacy)
        filename = f"raw_{portal_prefix}_{dev_slug}.json"
        file_path = self.dev_raw_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
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
        """Loads developer data from USIdev directory, with fallback to USIdata legacy location."""
        file_path = self.dev_dir / f"usi_dev_{dev_slug}.json"
        if not file_path.exists():
            # Fallback: legacy usi_dev_*.json stored inside USIdata/{slug}/
            file_path = self.data_dir / dev_slug / f"usi_dev_{dev_slug}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading developer file {file_path}: {e}")
            return None

    def list_developers(self) -> list:
        """Returns top-level developer data objects (children with parent_id excluded)."""
        developers = []
        for json_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    dev = json.load(f)
                if not dev.get("parent_id"):
                    developers.append(dev)
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")
        return developers

    def resolve_dev_slug(self, name: str) -> str:
        """Standardizes a developer name into a slug."""
        return slugify(name)

    def _append_event(self, dev: dict, event: dict):
        """Append to dev['events'] (newest first, max 100 entries)."""
        events = dev.setdefault("events", [])
        events.insert(0, {"at": datetime.now().isoformat(), **event})
        dev["events"] = events[:100]

    def merge_developers(self, target_slug: str, source_slug: str) -> bool:
        """
        Łączy source dewelopera z target deweloperem.

        Model: pliki NIE są usuwane ani archiwizowane.
        - source_dev.parent_id = target_dev.usi_dev_id  (hierarchia kaptiałowa)
        - portal_mapping source trafia do target (non-destructive)
        - target.merged_from[] przechowuje listę dzieci (cache)
        - Oba rekordy zostają w USIdev/ (legacy location w USIdata normalizowana)
        - list_developers() filtruje po parent_id == null
        """
        target_dev = self.get_developer(target_slug)
        source_dev = self.get_developer(source_slug)

        if not target_dev or not source_dev:
            logger.error(f"Merge failed: target={target_slug} found={target_dev is not None}, "
                         f"source={source_slug} found={source_dev is not None}")
            return False

        target_id = target_dev.get("usi_dev_id")
        if not target_id:
            logger.error(f"Merge failed: target {target_slug} has no usi_dev_id")
            return False

        # Set parent_id on source (this hides it from the main developer list)
        source_dev["parent_id"] = target_id

        # Enrich target portal_mapping with source mappings (non-destructive)
        target_mapping = target_dev.setdefault("portal_mapping", {})
        for portal, data in source_dev.get("portal_mapping", {}).items():
            if portal not in target_mapping:
                target_mapping[portal] = data
                logger.info(f"Merged {portal} mapping from {source_slug} to {target_slug}")

        # Enrich target metadata (non-destructive)
        target_meta = target_dev.setdefault("metadata", {})
        for k, v in source_dev.get("metadata", {}).items():
            if not target_meta.get(k) and v:
                target_meta[k] = v

        # Cache merged children on target (avoids full scan for detail view)
        merged_from = target_dev.setdefault("merged_from", [])
        if not any(m.get("slug") == source_slug for m in merged_from):
            merged_from.append({
                "slug": source_slug,
                "name": source_dev.get("name", source_slug),
                "usi_dev_id": source_dev.get("usi_dev_id"),
                "merged_at": datetime.now().isoformat(),
            })

        # Remove source from suggestions on target
        target_dev["suggestions"] = [
            s for s in target_dev.get("suggestions", [])
            if s.get("developer_slug") != source_slug
        ]

        # Events
        self._append_event(target_dev, {
            "type": "merge_in",
            "source_slug": source_slug,
            "source_name": source_dev.get("name", source_slug),
        })

        # Save target
        self.create_developer_file(target_dev)

        # Save source with parent_id set.
        # If source was in legacy USIdata location, normalize it to USIdev.
        legacy_path = self.data_dir / source_slug / f"usi_dev_{source_slug}.json"
        canonical_path = self.dev_dir / f"usi_dev_{source_slug}.json"
        try:
            canonical_path.write_text(
                json.dumps(source_dev, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if legacy_path.exists() and legacy_path != canonical_path:
                legacy_path.unlink()
                logger.info(f"Normalized {source_slug} dev file from USIdata to USIdev")
        except Exception as e:
            logger.error(f"Failed to save source {source_slug} with parent_id: {e}")

        logger.info(f"Linked {source_slug} → parent={target_slug} ({target_id})")
        return True

    def dismiss_suggestion(self, dev_slug: str, suggested_id: str) -> bool:
        """Removes a suggestion from developer record."""
        dev = self.get_developer(dev_slug)
        if not dev or "suggestions" not in dev:
            return False
        dismissed = next((s for s in dev["suggestions"] if s["usi_dev_id"] == suggested_id), None)
        new_suggestions = [s for s in dev["suggestions"] if s["usi_dev_id"] != suggested_id]
        if len(new_suggestions) == len(dev["suggestions"]):
            return False
        dev["suggestions"] = new_suggestions
        if dismissed:
            self._append_event(dev, {
                "type": "dismiss_suggestion",
                "dismissed_slug": dismissed.get("developer_slug"),
                "dismissed_id": suggested_id,
            })
        self.create_developer_file(dev)
        return True

    def unmerge_developer(self, target_slug: str, source_slug: str) -> bool:
        """
        Odłącza source_slug od target_slug.
        - Usuwa parent_id z rekordu source
        - Usuwa wpis ze merged_from[] na target
        - Portale przeniesione podczas merge NIE są cofane (zbyt ryzykowne)
        """
        target_dev = self.get_developer(target_slug)
        source_dev = self.get_developer(source_slug)
        if not target_dev or not source_dev:
            return False

        before = len(target_dev.get("merged_from", []))
        target_dev["merged_from"] = [
            m for m in target_dev.get("merged_from", [])
            if m.get("slug") != source_slug
        ]
        if len(target_dev.get("merged_from", [])) == before:
            return False

        source_dev.pop("parent_id", None)

        self._append_event(target_dev, {
            "type": "unmerge",
            "source_slug": source_slug,
            "source_name": source_dev.get("name", source_slug),
        })

        self.create_developer_file(target_dev)
        canonical_path = self.dev_dir / f"usi_dev_{source_slug}.json"
        try:
            canonical_path.write_text(
                json.dumps(source_dev, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save unmerged source {source_slug}: {e}")

        logger.info(f"Unlinked {source_slug} from {target_slug}")
        return True

    def find_by_portal_id(self, portal: str, portal_id: str) -> dict | None:
        """O(n) scan — finds developer with matching portal_mapping id/slug/agency_id."""
        pid = str(portal_id)
        for dev_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            pm = (data.get("portal_mapping") or {}).get(portal) or {}
            if (str(pm.get("id", "")) == pid
                    or str(pm.get("slug", "")) == pid
                    or str(pm.get("agency_id", "")) == pid):
                return data
            for aid in pm.get("agency_ids", []):
                if str(aid) == pid:
                    return data
        return None

    def log_event(self, dev_slug: str, event: dict) -> bool:
        """Append a generic event to the developer's event log."""
        dev = self.get_developer(dev_slug)
        if not dev:
            return False
        self._append_event(dev, event)
        self.create_developer_file(dev)
        return True
