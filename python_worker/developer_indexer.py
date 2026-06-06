import fcntl
import json
import logging
import re
import threading
from pathlib import Path
from datetime import datetime
from python_worker.slug_utils import slugify

_counter_lock = threading.Lock()
logger = logging.getLogger(__name__)

_global_identifiers_cache = None
_global_identifiers_cache_time = None

class DeveloperIndexer:

    def __init__(self, repo):
        self.repo = repo
        self.counters_path = Path(__file__).parent / "data" / "usi_counters.json"

    def _get_next_counter(self, key: str) -> int:
        """Atomic counter increment — thread-safe (threading.Lock) and process-safe (flock)."""
        self.counters_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.counters_path.exists():
            self.counters_path.write_text('{"dev": 0, "inv": 0, "dm": 0}', encoding="utf-8")
        with _counter_lock:
            with open(self.counters_path, "r+", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    data = json.load(f)
                    data[key] = data.get(key, 0) + 1
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
                    return data[key]
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)

    def generate_usi_id(self, prefix: str) -> str:
        """Generates a new USI ID (e.g., DEV-0001, INV-0001, DM-0001, IM-0001)."""
        key = {"DEV": "dev", "INV": "inv", "DM": "dm", "IM": "im"}.get(prefix, "dev")
        num = self._get_next_counter(key)
        return f"{prefix}-{num:04d}"

    # -------------------------------------------------------------------------
    # File path helpers
    # -------------------------------------------------------------------------

    def invalidate_identifiers_cache(self):
        global _global_identifiers_cache, _global_identifiers_cache_time
        _global_identifiers_cache = None
        _global_identifiers_cache_time = None

    def get_existing_identifiers(self) -> dict:
        """
        Retrieves existing investment identifiers using the investment index.
        ARCHITECTURAL MANDATE: No disk scanning during standard data retrieval.
        """
        global _global_identifiers_cache, _global_identifiers_cache_time
        
        now = datetime.now()
        if _global_identifiers_cache is not None and _global_identifiers_cache_time is not None:
            if (now - _global_identifiers_cache_time).total_seconds() < 300:
                return _global_identifiers_cache

        rp_ids = set()
        oto_ids = set()
        oto_slugs = set()
        to_ids = set()

        logger.info(f"Loading identifiers from investment index...")
        
        from python_worker.investment_index import load as load_index
        all_invs = load_index(self.repo.data_dir) or []

        for inv in all_invs:
            sources = inv.get("sources", {})
            if not sources:
                continue

            rp_src = sources.get("rp", {})
            if rp_src and rp_src.get("id"):
                val = str(rp_src["id"])
                if val and val != "None":
                    rp_ids.add(val)

            oto_src = sources.get("oto", {})
            if oto_src:
                if oto_src.get("id"):
                    val = str(oto_src["id"])
                    if val and val != "None":
                        oto_ids.add(val)
                url = oto_src.get("url")
                if url:
                    from .url_parser import parse_url
                    parsed = parse_url(url)
                    if parsed.get("investment_slug"):
                        full_slug = parsed["investment_slug"]
                        oto_slugs.add(full_slug)
                        # Extract ID from slug if present (canonical Otodom pattern)
                        if "-ID" in full_slug:
                            hash_id = full_slug.split("-ID")[-1]
                            oto_ids.add(hash_id)
                    if parsed.get("agency_id"):
                        oto_ids.add(parsed["agency_id"])

            to_src = sources.get("to", {})
            if to_src:
                if to_src.get("id"):
                    val = str(to_src["id"])
                    if val and val != "None":
                        to_ids.add(val)
                elif to_src.get("url"):
                    from .url_parser import parse_url
                    parsed = parse_url(to_src["url"])
                    if parsed.get("to_id"):
                        to_ids.add(str(parsed["to_id"]))

        logger.info(f"Found {len(rp_ids)} RP IDs, {len(oto_ids)} Otodom IDs, and {len(to_ids)} TO IDs via index.")
        result = {
            "rp_ids": rp_ids,
            "oto_ids": oto_ids,
            "oto_slugs": oto_slugs,
            "to_ids": to_ids,
        }
        _global_identifiers_cache_time = now
        _global_identifiers_cache = result
        return result

    # -------------------------------------------------------------------------
    # Raw file saves
    # -------------------------------------------------------------------------

    def find_developer_by_id(self, portal: str, portal_id: str) -> dict | None:
        """Finds a developer by its portal-specific ID (e.g., rp id, oto agency_id)."""
        if not portal or not portal_id:
            return None

        clean_id = str(portal_id).strip()
        if portal == "oto":
            clean_id = re.sub(r"^ID", "", clean_id)

        for dev in self.repo.list_developers(only_merged=False):
            pm = dev.get("portal_mapping", {})
            p_data = pm.get(portal)
            if not p_data:
                continue
            existing_id = p_data.get("id") or p_data.get("agency_id")
            if str(existing_id) == clean_id:
                return dev
            
            # Also check additional agency IDs
            for aid in p_data.get("agency_ids", []):
                if str(aid) == clean_id:
                    return dev
        return None

    def find_by_portal_id(self, portal: str, portal_id: str) -> dict | None:
        """O(n) scan — finds developer with matching portal_mapping id/slug/agency_id."""
        pid = str(portal_id)
        seen_slugs = set()
        for pattern in ("*/usi_dev_*.json", "usi_dev_*.json"):
            for dev_file in self.repo.dev_dir.glob(pattern):
                try:
                    data = json.loads(dev_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                slug = data.get("developer_slug", "")
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                pm = (data.get("portal_mapping") or {}).get(portal) or {}
                if (str(pm.get("id", "")) == pid
                        or str(pm.get("slug", "")) == pid
                        or str(pm.get("agency_id", "")) == pid):
                    return data
                for aid in pm.get("agency_ids", []):
                    if str(aid) == pid:
                        return data
        return None

    # -------------------------------------------------------------------------
    # Generic event log
    # -------------------------------------------------------------------------

_shared_index_instance = None
_shared_index_mtime = 0

def get_shared_developer_index():
    """
    Returns a RAM-cached version of the developer index for O(1) lookups.
    Used by DeveloperRepository to avoid disk scans.
    """
    global _shared_index_instance, _shared_index_mtime
    from python_worker.config import USI_DEV_DIR
    from . import developer_index
    
    path = developer_index._index_path(USI_DEV_DIR)
    mtime = 0
    if path.exists():
        try:
            mtime = path.stat().st_mtime
        except OSError:
            pass
    
    if _shared_index_instance is None or _shared_index_mtime != mtime:
        class RAMDeveloperIndex:
            def __init__(self, dev_dir, mtime):
                self.mtime = mtime
                entries = developer_index.load(dev_dir) or []
                self._id_map = {e.get("usi_dev_id"): e for e in entries if e.get("usi_dev_id")}
                
            def get_developer(self, usi_dev_id: str) -> dict | None:
                return self._id_map.get(usi_dev_id)
                
            def list_developers(self):
                return list(self._id_map.values())
                
        _shared_index_instance = RAMDeveloperIndex(USI_DEV_DIR, mtime)
        _shared_index_mtime = mtime
        
    return _shared_index_instance
