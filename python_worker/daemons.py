import logging
from pathlib import Path
import json

from python_worker.config import USI_DATA_DIR, USI_DEV_DIR, get_scraper_config
from python_worker.developer_manager import DeveloperManager
from python_worker.services.developer_service import DeveloperService
from python_worker.services.discovery_service import DiscoveryService
from python_worker.url_parser import parse_url
from python_worker.logger_utils import log_to_dev_log

try:
    from usi_crawlers.wedrowiec import WedrowiecDaemon
    from usi_crawlers.doktor import DoktorDaemon, DoktorDelegate
    from usi_crawlers.algorithms.similarity import normalize_name
    HAS_CRAWLERS = True
except ImportError:
    HAS_CRAWLERS = False

logger = logging.getLogger(__name__)

def _build_dismissed_cache(dev_dir: Path) -> dict[str, set[str]]:
    cache: dict[str, set[str]] = {}
    central = dev_dir / "dismissed_pairs.jsonl"
    if central.exists():
        for line in central.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                dismisser = e.get("dismisser_id")
                dismissed = e.get("dismissed_id")
                if dismisser and dismissed:
                    cache.setdefault(dismisser, set()).add(dismissed)
            except Exception:
                continue
    else:
        for master_file in dev_dir.glob("*/dev_master_*.json"):
            try:
                master = json.loads(master_file.read_text(encoding="utf-8"))
                owner_id = master.get("master_usi_dev_id")
                if owner_id:
                    cache[owner_id] = {
                        d["usi_dev_id"] for d in master.get("dismissed", [])
                        if d.get("usi_dev_id")
                    }
            except Exception:
                continue
    return cache

class TrackerDoktorDelegate:
    def __init__(self, data_dir: Path, dev_dir: Path):
        self.dm = DeveloperManager(data_dir, dev_dir)
        self.dev_dir = dev_dir
        self.data_dir = data_dir

    def get_developers_for_analysis(self) -> list[dict]:
        devs = self.dm.list_developers()
        processed = []
        for d in devs:
            slug = d["developer_slug"]
            norm = normalize_name(d["name"]) if HAS_CRAWLERS else d["name"]
            buckets = {}
            cities = set()
            
            dev_path = self.data_dir / slug
            if dev_path.exists():
                import json
                from python_worker.api.utils import _find_inv_file
                for inv_dir in dev_path.iterdir():
                    if not inv_dir.is_dir(): continue
                    usi_file = _find_inv_file(inv_dir, inv_dir.name)
                    if usi_file and usi_file.exists():
                        try:
                            with open(usi_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                coords = data.get("location", {}).get("coords")
                                city = data.get("location", {}).get("city")
                                if city:
                                    cities.add(city.strip().lower())
                                    
                                specs = data.get("specifications", {})
                                year = specs.get("delivery_year")
                                quarter = specs.get("delivery_quarter")
                                
                                if coords and len(coords) == 2:
                                    lat, lon = coords
                                    # SKIP Null Island [0, 0] to prevent suggestion flooding
                                    if lat == 0 and lon == 0:
                                        continue
                                        
                                    bkey = f"{round(lat, 2):.2f}_{round(lon, 2):.2f}"
                                    if bkey not in buckets: buckets[bkey] = []
                                    buckets[bkey].append({
                                        "lat": lat, "lon": lon, 
                                        "year": int(year) if year else None,
                                        "quarter": int(quarter) if quarter else None
                                    })
                        except Exception: continue

            # Prevent generic collisions on empty or very short names
            if norm and len(norm) < 3:
                norm = None

            processed.append({
                "id": d["usi_dev_id"],
                "slug": slug,
                "name": d["name"],
                "norm": norm,
                "buckets": buckets,
                "cities": cities,
                "parent_id": d.get("parent_id"),
                "master_id": d.get("master_id")
            })
        return processed

    def get_dismissed_cache(self) -> dict[str, set[str]]:
        return _build_dismissed_cache(self.dev_dir)

    def save_suggestions(self, dev_id: str, suggestions: list[dict]):
        fresh_dev = self.dm.get_developer_by_id(dev_id)
        if fresh_dev:
            # Map input suggestions to our storage format
            new_suggestions = {}
            for s in suggestions:
                new_suggestions[s["target_id"]] = {
                    "usi_dev_id": s["target_id"],
                    "developer_slug": s["target_slug"],
                    "reason": s["reason"],
                    "score": s["score"]
                }
            
            # Merge with existing (preserve existing, update with new if better)
            existing = fresh_dev.get("suggestions", [])
            merged = {s["usi_dev_id"]: s for s in existing}
            merged.update(new_suggestions)
            
            fresh_dev["suggestions"] = list(merged.values())
            self.dm.create_developer_file(fresh_dev)

_doktor_instance = None
_crawler_instance = None

def init_doktor(data_dir: Path, dev_dir: Path):
    global _doktor_instance
    if HAS_CRAWLERS:
        delegate = TrackerDoktorDelegate(data_dir, dev_dir)
        _doktor_instance = DoktorDaemon(delegate)
    return _doktor_instance

def get_doktor():
    return _doktor_instance

def init_crawler(data_dir: Path, dev_dir: Path):
    global _crawler_instance
    if HAS_CRAWLERS:
        context = {
            "data_dir": data_dir,
            "dev_dir": dev_dir,
            "developer_manager": DeveloperManager(data_dir, dev_dir),
            "developer_service": DeveloperService(data_dir, dev_dir),
            "discovery_service": DiscoveryService(data_dir),
            "get_scraper_config": get_scraper_config,
            "parse_url": parse_url,
            "log_to_dev_log": log_to_dev_log
        }
        _crawler_instance = WedrowiecDaemon(context)
    return _crawler_instance

def get_crawler():
    return _crawler_instance
