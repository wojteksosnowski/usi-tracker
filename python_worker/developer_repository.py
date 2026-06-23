import json
import logging
import re
import threading
from pathlib import Path
from datetime import datetime
from python_worker.slug_utils import slugify
from usi_scrapers import api as scraper_api
from python_worker.utils import write_json_atomically

_counter_lock = threading.Lock()
logger = logging.getLogger(__name__)

class DeveloperRepository:

    def __init__(self, data_dir: Path, dev_dir: Path = None):
        self.data_dir = Path(data_dir) if isinstance(data_dir, str) else data_dir
        self.dev_dir = Path(dev_dir) if dev_dir else (self.data_dir.parent / "USIdev")
        self.dev_raw_dir = self.dev_dir / "raw"
        try:
            self.dev_dir.mkdir(parents=True, exist_ok=True)
            self.dev_raw_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Note: Could not verify/create directories {self.dev_dir} or {self.dev_raw_dir} due to OS permissions. Proceeding anyway. Error: {e}")
        self.counters_path = Path(__file__).parent / "data" / "usi_counters.json"

        from python_worker.config import get_shared_tech_manager
        self.tech_manager = get_shared_tech_manager()

    def _dev_file_path(self, dev_slug: str, usi_dev_id: str = None) -> Path | None:
        """New-format path: USIdev/{slug}/usi_dev_{usi_dev_id}_{slug}.json
        Returns None if no existing file found via glob (when usi_dev_id not given)."""
        subdir = self.dev_dir / dev_slug
        if usi_dev_id:
            return subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
        if subdir.exists():
            candidates = sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json"))
            if candidates:
                return candidates[0]
        return None

    def _dev_file_path_old_canonical(self, dev_slug: str) -> Path:
        """Pre-ID canonical path: USIdev/{slug}/usi_dev_{slug}.json"""
        return self.dev_dir / dev_slug / f"usi_dev_{dev_slug}.json"

    def _dev_file_path_legacy(self, dev_slug: str) -> Path:
        """Flat legacy path: USIdev/usi_dev_{dev_slug}.json"""
        return self.dev_dir / f"usi_dev_{dev_slug}.json"

    def _dev_master_path(self, master_id: str, master_slug: str) -> Path:
        return self.dev_dir / master_slug / f"dev_master_{master_id}.json"

    # -------------------------------------------------------------------------
    # Level 3 (dev_master) helpers
    # -------------------------------------------------------------------------

    def _read_dev_master(self, master_id: str) -> dict | None:
        from python_worker import developer_index
        master_idx = developer_index.load_master_index(self.dev_dir)
        
        target_path = None
        if master_idx and master_id in master_idx:
            folder = master_idx[master_id].get("path")
            if folder:
                target_path = self._dev_master_path(master_id, folder)
                
        if not target_path or not target_path.exists():
            # Fallback global glob
            for p in self.dev_dir.glob(f"*/dev_master_{master_id}.json"):
                target_path = p
                break
                
        if not target_path or not target_path.exists():
            return None
            
        try:
            return json.loads(target_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not read dev_master {target_path}: {e}")
            return None

    def _save_dev_master(self, master: dict, master_slug: str) -> None:
        path = self._dev_master_path(master["dev_master_id"], master_slug)
        write_json_atomically(path, master)
        
        from python_worker import developer_index
        developer_index.upsert_master(self.dev_dir, master, master_slug)

    def _get_or_create_dev_master(self, master_slug: str, master_dev: dict) -> dict:
        """Reads existing dev_master or creates a new one; sets master_id on master_dev in-place."""
        master_id = master_dev.get("master_id")
        if master_id:
            existing = self._read_dev_master(master_id)
            if existing:
                return existing
        dm_id = self.generate_usi_id("DM")
        master = {
            "dev_master_id": dm_id,
            "master_usi_dev_id": master_dev.get("usi_dev_id"),
            "master_slug": master_slug,
            "merged_from": [],
            "dismissed": [],
        }
        master_dev["master_id"] = dm_id
        return master

    def generate_usi_id(self, prefix: str) -> str:
        from python_worker.developer_indexer import DeveloperIndexer
        return DeveloperIndexer(self).generate_usi_id(prefix)

    # -------------------------------------------------------------------------
    # Log helpers
    # -------------------------------------------------------------------------

    def append_dev_log(self, dev_slug: str, event: dict) -> None:
        """Appends one JSONL event to dev_log_{slug}.txt."""
        log_path = self.dev_dir / dev_slug / f"dev_log_{dev_slug}.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": datetime.now().isoformat(), **event}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _append_event(self, dev: dict, event: dict):
        """Deprecated shim — logs to dev_log_*.txt instead of dev['events']."""
        dev_slug = dev.get("developer_slug")
        if dev_slug:
            self.append_dev_log(dev_slug, event)

    # -------------------------------------------------------------------------
    # Identifiers scan (investment files)
    # -------------------------------------------------------------------------

    def save_raw_json(self, data: dict, portal_id: str, portal_prefix: str) -> Path:
        """Delegates raw investment JSON saving to the library manager."""
        if not self.tech_manager:
            raise RuntimeError("Strict immutability rule: raw files MUST be managed via TechnicalDataManager. Library not configured.")
        return scraper_api.save_raw(self.tech_manager.config, data, portal_prefix, portal_id=portal_id)

    def save_discovery_snapshot(self, system_id: str, items: list[dict]):
        """Saves discovery results to a JSON file in the developer's directory."""
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(self.data_dir, self.dev_dir)
        dev = dm.get_developer_by_id(system_id)
        if dev and dev.get("directory"):
             dev_dir = dev["directory"]
             dev_slug = dev.get("developer_slug", system_id)
        else:
             # Fallback
             dev_slug = system_id
             dev_dir = self.dev_dir / dev_slug

        dev_dir.mkdir(parents=True, exist_ok=True)
        discovery_file = dev_dir / "discovery.json"

        data = {
            "system_id": system_id,
            "dev_slug": dev_slug,
            "checked_at": __import__("datetime").datetime.now().isoformat(),
            "items": items
        }
        with open(discovery_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return discovery_file
    def save_dev_raw_json(self, data: dict, portal_prefix: str, portal_id: str) -> Path:
        """Delegates raw developer JSON saving to the library manager."""
        if not self.tech_manager:
            raise RuntimeError("Strict immutability rule: raw files MUST be managed via TechnicalDataManager. Library not configured.")
        return scraper_api.save_raw_developer(self.tech_manager.config, data, portal_prefix, portal_id=portal_id)

    # -------------------------------------------------------------------------
    # Core CRUD — Level 2 files
    # -------------------------------------------------------------------------

    def create_developer_file(self, developer_data: dict) -> Path:
        """
        Creates or updates usi_dev_{usi_dev_id}_{slug}.json in USIdev/{slug}/.
        Strips events[] and merged_from[] — those belong in Level 3 / log files.
        Auto-removes the pre-ID old-format file if present.
        """
        dev_slug = developer_data.get("developer_slug")
        if not dev_slug:
            raise ValueError("developer_slug is required")

        subdir = self.dev_dir / dev_slug
        subdir.mkdir(parents=True, exist_ok=True)

        # Load existing data for audit/id preservation.
        # MANDATE: Search strictly by original portal ID.
        existing_data = {}
        incoming_pm = developer_data.get("portal_mapping") or {}
        
        # Identification key: take first non-empty portal and its technical ID
        incoming_portal = next((p for p in ("rp", "oto", "to") if incoming_pm.get(p)), None)

        if incoming_portal:
            target_id = (incoming_pm[incoming_portal].get("id") 
                         if incoming_portal == "rp" 
                         else incoming_pm[incoming_portal].get("agency_id"))
            
            # Scan directory for a file containing the EXACT same original portal ID
            for f in sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json")):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    curr_pm = d.get("portal_mapping", {}).get(incoming_portal, {})
                    curr_id = curr_pm.get("id") if incoming_portal == "rp" else curr_pm.get("agency_id")
                    
                    if str(curr_id) == str(target_id) and target_id:
                        existing_data = d
                        break
                except Exception as e:
                    logger.warning(f"Error verifying portal ID in {f}: {e}")
        else:
            # Fallback for records without portal mapping (e.g. manual merges)
            for candidate in [
                self._dev_file_path(dev_slug),
                self._dev_file_path_old_canonical(dev_slug),
                self._dev_file_path_legacy(dev_slug),
            ]:
                if candidate and candidate.exists():
                    try:
                        existing_data = json.loads(candidate.read_text(encoding="utf-8"))
                        break
                    except Exception as e:
                        logger.warning(f"Could not read existing dev file {candidate}: {e}")

        # Ensure portal_mapping exists
        if "portal_mapping" not in developer_data:
            developer_data["portal_mapping"] = existing_data.get("portal_mapping", {
                "rp": None, "oto": None, "to": None
            })

        # Preserve audit timestamps
        developer_data["audit"] = existing_data.get("audit", {
            "created_at": datetime.now().isoformat()
        })
        developer_data["audit"]["updated_at"] = datetime.now().isoformat()

        # Ensure usi_dev_id
        if not developer_data.get("usi_dev_id"):
            if existing_data.get("usi_dev_id"):
                developer_data["usi_dev_id"] = existing_data["usi_dev_id"]
            else:
                developer_data["usi_dev_id"] = self.generate_usi_id("DEV")

        # --- MIGRACJA: Spłaszczanie danych z 'crawler' (Level 2) ---
        # Przenosimy dane z zagnieżdżonego słownika do korzenia rekordu.
        crawler = developer_data.get("crawler") or existing_data.get("crawler")
        if isinstance(crawler, dict):
            if "last_maintenance" in crawler and "last_maintenance" not in developer_data:
                developer_data["last_maintenance"] = crawler["last_maintenance"]
            if "new_since_review" in crawler and "new_since_review" not in developer_data:
                developer_data["new_since_review"] = crawler["new_since_review"]
            if "maintenance_success" in crawler and "maintenance_success" not in developer_data:
                developer_data["maintenance_success"] = crawler["maintenance_success"]
        
        # Usuwamy sekcję crawler — jest już niekompatybilna z nowym modelem pasywnym
        developer_data.pop("crawler", None)

        # Strip Level 3 fields — they live in dev_master_*.json
        # NOTE: parent_id (hierarchy) is preserved in Level 2 as per schema.
        developer_data.pop("events", None)
        developer_data.pop("merged_from", None)
        developer_data.pop("is_master", None)
        developer_data.pop("is_child", None)
        developer_data.pop("original_portal_mapping", None)
        developer_data.pop("investments_count", None)
        developer_data.pop("resources", None)
        developer_data.pop("suggestions", None)

        usi_dev_id = developer_data["usi_dev_id"]
        
        # New naming convention: usi_dev_{portal}_{portal_id}.json
        portal = incoming_portal or "unknown"
        portal_id = "unknown"
        if incoming_portal:
            p_data = incoming_pm[incoming_portal]
            portal_id = p_data.get("id") or p_data.get("agency_id") or "unknown"
        
        file_path = subdir / f"usi_dev_{portal}_{portal_id}.json"
        write_json_atomically(file_path, developer_data)

        # Clean up any files with the same USI ID but different portal/portal_id in the same directory
        # (Since we just saved the authoritative record for this portal)
        for old_id_file in subdir.glob(f"usi_dev_{usi_dev_id}_*.json"):
            try:
                old_id_file.unlink()
                logger.info(f"Removed old-format file with ID: {old_id_file}")
            except Exception: pass

        logger.info(f"Saved developer file: {file_path}")
        
        # Update index
        from . import developer_index
        developer_index.upsert(self.data_dir, self.dev_dir, dev_slug, usi_dev_id)

        return file_path

    def _find_anchor_by_id(self, usi_dev_id: str) -> Path | None:
        """Locates the developer anchor file by USI-DEV-ID.
        With the new naming convention (usi_dev_{portal}_{portal_id}.json),
        this requires an index lookup or a scan since ID is no longer in the filename.
        """
        if not usi_dev_id:
            return None

        # 1. Try RAM index first (Fastest)
        try:
            from . import developer_index
            idx = developer_index.load(self.dev_dir)
            if idx:
                entry = next((e for e in idx if e.get("usi_dev_id") == usi_dev_id), None)
                if entry and entry.get("developer_slug"):
                    subdir = self.dev_dir / entry["developer_slug"]
                    if subdir.exists():
                        for f in subdir.glob("usi_dev_*.json"):
                            try:
                                d = json.loads(f.read_text(encoding="utf-8"))
                                if d.get("usi_dev_id") == usi_dev_id:
                                    return f
                            except Exception: continue
        except Exception: pass

        # 2. Fallback: Full Scan (Slow path - O(N))
        # This is the last resort if index is missing or stale.
        for f in self.dev_dir.glob("*/usi_dev_*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.get("usi_dev_id") == usi_dev_id:
                    return f
            except Exception: continue

        return None

    def get_developer(self, usi_dev_id: str, identifiers: dict = None) -> dict | None:
        """Loads developer data. Returns merged view: Level 2 + merged_from from Level 3.
        MANDATE: ID-ONLY. Only accepts USI IDs (DEV-...)."""
        if not usi_dev_id or not str(usi_dev_id).startswith("DEV-"):
            return None
            
        # Try O(1) index lookup first
        from . import developer_index
        index = developer_index.load(self.dev_dir)
        if index:
            entry = next((e for e in index if e.get("usi_dev_id") == usi_dev_id), None)
            if entry:
                return self._enrich_with_master(entry, identifiers)

        # Fallback to direct disk lookup by ID
        return self.get_developer_by_id(usi_dev_id)

    def get_developer_by_id(self, usi_dev_id: str) -> dict | None:
        """Find developer by usi_dev_id. Fast path uses ID embedded in new filename."""
        anchor = self._find_anchor_by_id(usi_dev_id)
        if not anchor:
            return None
            
        try:
            dev = json.loads(anchor.read_text(encoding="utf-8"))
            resources = self.get_developer_resources(usi_dev_id)
            if resources:
                files_dict = {}
                for k, v in resources.get("files", {}).items():
                    if v is None: continue
                    if isinstance(v, list):
                        files_dict[k] = [str(p) for p in v]
                    else:
                        files_dict[k] = str(v)
                dev["resources"] = {
                    "base_dir": str(resources["base_dir"]),
                    "files": files_dict
                }
            return self._enrich_with_master(dev)
        except Exception:
            return None

    def get_developer_resources(self, usi_dev_id: str) -> dict | None:
        """
        Universal ID-to-File mapping for developers.
        Returns a map of all physical files associated with a USI Developer ID.
        
        ARCHITECTURAL MANDATE: ID-ONLY PRIORITY.
        This method is the authoritative way to locate developer resources (Level 2 & 3).
        Always resolve physical paths via this resolver using USI-DEV-ID.
        """
        from . import developer_index
        index = developer_index.load(self.dev_dir)
        
        entry = None
        if index:
            entry = next((e for e in index if e.get("usi_dev_id") == usi_dev_id), None)
        
        if not entry:
            # Fallback direct lookup
            anchor = self._find_anchor_by_id(usi_dev_id)
            if not anchor:
                return None
            try:
                entry = json.loads(anchor.read_text(encoding="utf-8"))
            except Exception:
                return None

        dev_slug = entry.get("developer_slug")
        if not dev_slug:
            return None

        subdir = self.dev_dir / dev_slug
        
        # Determine anchor file precisely
        anchor_file = subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
        if not anchor_file.exists():
            # Search for any file with this ID in this folder
            matches = list(subdir.glob(f"usi_dev_{usi_dev_id}_*.json"))
            if matches:
                anchor_file = matches[0]
            else:
                anchor_file = self._find_anchor_by_id(usi_dev_id)

        # Determine master file
        master_file = None
        master_id = entry.get("master_id")
        if master_id:
            master_file = self._dev_master_path(master_id, dev_slug)
            if not master_file.exists():
                # Fallback glob
                for p in self.dev_dir.glob(f"*/dev_master_{master_id}.json"):
                    master_file = p
                    break

        # Log file
        log_file = subdir / f"dev_log_{dev_slug}.txt"

        return {
            "id": usi_dev_id,
            "type": "developer",
            "base_dir": subdir,
            "files": {
                "anchor": anchor_file if anchor_file and anchor_file.exists() else None,
                "master": master_file if master_file and master_file.exists() else None,
                "logs": [log_file] if log_file.exists() else []
            },
            "metadata": {
                "slug": dev_slug,
                "master_id": master_id,
                "name": entry.get("name")
            }
        }

    def list_developers(self, only_merged: bool = False, identifiers: dict = None) -> list:
        """Returns top-level developer records; merged-source children excluded."""
        from . import developer_index
        indexed = developer_index.load(self.dev_dir)
        
        developers = []
        seen_ids: set[str] = set()

        def _should_include(dev: dict, child_ids_set: set[str] = None) -> bool:
            dev_id = dev.get("usi_dev_id", "")
            if dev_id in seen_ids:
                return False
            seen_ids.add(dev_id)

            # Determine if this dev is a child.
            # If using index, we rely on is_child set by _enrich_with_master,
            # or parent_id, or if we have child_ids_set from dev_master scanning.
            is_child = dev.get("parent_id") or dev.get("is_child", False)
            if not is_child and child_ids_set is not None:
                is_child = dev_id in child_ids_set

            if is_child:
                return False

            if only_merged:
                has_master = bool(dev.get("master_id") or dev.get("merged_from"))
                pm = dev.get("portal_mapping", {})
                has_mapping = any(pm.get(p) for p in ("rp", "oto", "to"))
                if not (has_master or has_mapping):
                    return False

            return True

        if indexed is not None:
            # Fast path: filter from in-memory index
            for dev in indexed:
                if _should_include(dev):
                    developers.append(dev)
            return developers

        # Fallback: disk scan
        # Build child IDs from all dev_master files — children are listed in merged_from[]
        child_ids: set[str] = set()
        for master_file in self.dev_dir.glob("*/dev_master_*.json"):
            try:
                master = json.loads(master_file.read_text(encoding="utf-8"))
                for m in master.get("merged_from", []):
                    if cid := m.get("usi_dev_id"):
                        child_ids.add(cid)
            except Exception:
                pass

        def _add(dev: dict) -> None:
            dev = self._enrich_with_master(dev, identifiers)
            if _should_include(dev, child_ids):
                developers.append(dev)

        for json_file in self.dev_dir.glob("*/usi_dev_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    _add(json.load(f))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        # Legacy flat files not yet migrated
        for json_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    _add(json.load(f))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        # Legacy format inside USIdata/
        for json_file in self.data_dir.glob("*/usi_dev_*.json"):
            if re.match(r"usi_dev_[A-Z]+-\d+_", json_file.name):
                continue
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    _add(json.load(f))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        return developers

    def get_total_pending_count(self, identifiers: dict) -> int:
        """Returns sum of unregistered investments for all active developers."""
        from .services.discovery_service import DiscoveryService
        from . import developer_index
        
        # Pobieramy deweloperów z indeksu - to jest błyskawiczne (RAM)
        indexed = developer_index.load(self.dev_dir)
        if not indexed:
            return 0

        try:
            from python_worker.developer_manager import DeveloperManager
            dm = DeveloperManager(self.data_dir)
        except Exception:
            return 0

        total = 0
        seen_slugs = set()
        
        for dev in indexed:
            # Omijamy dzieci (merged_from)
            if dev.get("parent_id") or dev.get("is_child"):
                continue
                
            slug = dev.get("developer_slug")
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            
            # KRYTYCZNA OPTYMALIZACJA: Przekazujemy ścieżkę do DeveloperManager,
            # zamiast pozwalać mu wywoływać get_developer_by_id tysiące razy.
            # Próbujemy znaleźć katalog dewelopera (powinien być w USIdata/slug)
            dev_dir = self.data_dir / slug
            if dev_dir.is_dir():
                total += dm.get_unregistered_count_from_dir(dev_dir, identifiers)
                
        return total

    # -------------------------------------------------------------------------
    # Merge / Unmerge
    # -------------------------------------------------------------------------

    def log_event(self, usi_dev_id: str, event: dict) -> bool:
        """Append a generic event to the developer's log file."""
        anchor = self._find_anchor_by_id(usi_dev_id)
        if not anchor:
            return False
        
        # Get slug from anchor parent directory
        dev_slug = anchor.parent.name
        self.append_dev_log(dev_slug, event)
        return True

    def _enrich_with_master(self, dev: dict, identifiers: dict = None) -> dict:
        """Add merged_from from Level 3, aggregate portal mappings, count investments & set mtime."""
        master_id = dev.get("master_id")
        if master_id:
            master = self._read_dev_master(master_id)
            if master and dev.get("usi_dev_id") == master.get("master_usi_dev_id"):
                dev["merged_from"] = master.get("merged_from", [])
                dev["suggestions"] = master.get("suggestions", [])
                dev["is_master"] = True
            else:
                dev.setdefault("merged_from", [])
                dev.setdefault("suggestions", [])
                dev["is_child"] = True
        else:
            dev.setdefault("merged_from", [])
            dev.setdefault("suggestions", [])

        # Process investment stats and aggregated portal_mapping
        base_id = dev.get("usi_dev_id")
        base_slug = dev.get("developer_slug", "")
        base_pm = dev.get("portal_mapping") or {}
        dev["original_portal_mapping"] = base_pm.copy()
        aggregated_pm = base_pm.copy()
        
        all_mtimes = []
        total_count = 0
        existing_inv_ids = set()
        investment_summary = []

        def _process_id(did: str):
            nonlocal total_count
            invs = self._inv_by_dev_id.get(did, [])
            for i in invs:
                ci_id = i.get("usi_inv_id")
                if ci_id and ci_id not in existing_inv_ids:
                    total_count += 1
                    existing_inv_ids.add(ci_id)
                elif not ci_id:
                    total_count += 1
                
                # Investment summary for index-based similarity matching
                investment_summary.append({
                    "slug": i.get("slug"),
                    "coordinates": i.get("coordinates") or i.get("coords")
                })

                # Dynamically infer portal from investment
                src = (i.get("source") or i.get("portal") or "").lower()
                if src in ("rp", "oto", "to"):
                    if not aggregated_pm.get(src):
                        aggregated_pm[src] = {"_inferred": True}
                
                ts = i.get("last_updated_ts")
                if ts:
                    all_mtimes.append(ts)

        if base_id:
            _process_id(base_id)

        # MANDAT ID-ONLY (Uzupełnienie): O(1) Lookup zamiast pętli O(I)
        # Służy to poprawieniu statystyk w widoku listy dla deweloperów z niepełnym backfillem ID.
        for portal in ("rp", "oto", "to"):
            pm_p = aggregated_pm.get(portal)
            if not pm_p: continue
            
            p_ids = []
            if portal == "rp" and pm_p.get("id"): p_ids.append(str(pm_p["id"]))
            elif portal == "oto":
                p_ids.extend([str(a) for a in (pm_p.get("agency_ids") or [pm_p.get("agency_id", "")]) if a])
                if pm_p.get("id"): p_ids.append(str(pm_p["id"]))
            elif portal == "to":
                val = pm_p.get("id") or pm_p.get("slug") or pm_p.get("agency_id")
                if val: p_ids.append(str(val))
                
            for p_id in p_ids:
                for i in self._inv_by_portal_id.get(portal, {}).get(p_id, []):
                    ci_id = i.get("usi_inv_id")
                    if ci_id and ci_id in existing_inv_ids: continue
                    # Add it
                    total_count += 1
                    if ci_id: existing_inv_ids.add(ci_id)
                    investment_summary.append({
                        "slug": i.get("slug"),
                        "coordinates": i.get("coordinates") or i.get("coords")
                    })
                    ts = i.get("last_updated_ts")
                    if ts: all_mtimes.append(ts)

        # Process merged members
        for member in dev.get("merged_from", []):
            mid = member.get("usi_dev_id")
            if mid:
                _process_id(mid)
                # Aggregate portal mappings from children
                child_record = self.get_developer_by_id(mid)
                if child_record:
                    child_pm = child_record.get("portal_mapping") or {}
                    for p in ("rp", "oto", "to"):
                        if not aggregated_pm.get(p) and child_pm.get(p):
                            aggregated_pm[p] = child_pm[p]
        
        dev["portal_mapping"] = aggregated_pm
        dev["investments_count"] = total_count
        dev["investments"] = investment_summary
        dev["last_updated"] = max(all_mtimes) if all_mtimes else None
        
        # 3. Crawler & Discovery stats
        dev["new_since_review"] = dev.get("new_since_review", 0)
        
        # 4. Maintenance Score (Przeniesione do DeveloperService)
        dev["maintenance_overdue_score"] = 0
        dev["unregistered_count"] = 0

        return dev

    @property
    def _inv_by_portal_id(self):
        if not hasattr(self, "_cached_inv_by_portal_id"):
            self._cached_inv_by_portal_id = {"rp": {}, "oto": {}, "to": {}}
            for inv in self._inv_index_data:
                src = inv.get("sources") or {}
                for p in ("rp", "oto", "to"):
                    if p not in src: continue
                    p_info = src[p]
                    # Map multiple possible ID keys to the same portal bucket
                    keys = ["id", "vendor_id", "agency_id", "developer_id"]
                    for k in keys:
                        val = p_info.get(k)
                        if val:
                            self._cached_inv_by_portal_id[p].setdefault(str(val), []).append(inv)
                    
                    # Handle agency_ids list for Otodom
                    if p == "oto" and "agency_ids" in p_info:
                        for aid in p_info["agency_ids"]:
                            if aid:
                                self._cached_inv_by_portal_id[p].setdefault(str(aid), []).append(inv)
        return self._cached_inv_by_portal_id



    @property
    def _inv_index_data(self):
        if not hasattr(self, "_cached_inv_index"):
            from python_worker.investment_index import load as load_inv_index
            self._cached_inv_index = load_inv_index(self.data_dir) or []
        return self._cached_inv_index

    @property
    def _inv_by_dev_id(self):
        """Groups all investments by their usi_dev_id (ID-only rule)."""
        if not hasattr(self, "_cached_inv_by_id"):
            self._cached_inv_by_id = {}
            for inv in self._inv_index_data:
                did = inv.get("usi_dev_id")
                if did:
                    self._cached_inv_by_id.setdefault(did, []).append(inv)
        return self._cached_inv_by_id

    def _inv_matches_dev(self, inv: dict, pm: dict) -> bool:
        src = inv.get("sources") or {}
        for portal in ("rp", "oto", "to"):
            if not pm.get(portal) or not src.get(portal):
                continue
            pm_p = pm[portal]
            src_p = src[portal]
            if pm_p.get("_inferred"): return True
            if portal == "rp":
                if str(pm_p.get("id", "")) == str(src_p.get("vendor_id", "")) and pm_p.get("id"): return True
            elif portal == "oto":
                pm_aids = {str(a) for a in (pm_p.get("agency_ids") or [pm_p.get("agency_id", "")]) if a}
                if str(src_p.get("agency_id", "")) in pm_aids and src_p.get("agency_id"): return True
            elif portal == "to":
                pm_id = str(pm_p.get("id") or pm_p.get("slug", "") or pm_p.get("agency_id", ""))
                src_id = str(src_p.get("developer_id") or "")
                if (pm_id == src_id and pm_id) or (not pm_id and not src_id): return True
        return False
