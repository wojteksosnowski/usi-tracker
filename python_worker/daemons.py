import logging
import time
from pathlib import Path
import json

from python_worker.config import USI_DATA_DIR, USI_DEV_DIR, get_shared_config
from python_worker.developer_manager import DeveloperManager
from python_worker.services.developer_service import DeveloperService
from python_worker.services.discovery_service import DiscoveryService
from python_worker.url_parser import parse_url
from python_worker.logger_utils import log_to_dev_log

try:
    from usi_crawlers.wedrowiec import WedrowiecDaemon
    from usi_crawlers.doktor import DoktorDaemon, DoktorDelegate
    HAS_CRAWLERS = True
except ImportError:
    HAS_CRAWLERS = False

# Local similarity algorithms
from python_worker.algorithms.similarity.engine import calculate_similarities
from python_worker.algorithms.similarity.strategies import normalize_name

logger = logging.getLogger(__name__)

from typing import Optional, Any

def safe_round(value: Any, digits: int = 2) -> Optional[float]:
    """
    Bezpieczna funkcja zaokrąglająca. 
    Zapobiega awarii typu: type NoneType doesn't define __round__ method.
    """
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (ValueError, TypeError):
        return None

def run_manual_doktor_analysis(data_dir: Path, dev_dir: Path):
    """Performs a one-off similarity analysis and saves results without a daemon."""
    logger.info("Starting manual developer similarity analysis...")
    start_t = time.time()
    
    try:
        delegate = TrackerDoktorDelegate(data_dir, dev_dir)
        devs = delegate.get_developers_for_analysis()
        dismissed = delegate.get_dismissed_cache()
        
        # Run the algorithm
        suggestions = calculate_similarities(devs, dismissed)
        
        # Deduplicate and group by source_id
        unique_suggestions = {}
        for s in suggestions:
            key = (s["source_id"], s["target_id"])
            if key not in unique_suggestions or s["score"] > unique_suggestions[key]["score"]:
                unique_suggestions[key] = s
        
        grouped = {}
        for s in unique_suggestions.values():
            grouped.setdefault(s["source_id"], []).append({
                "target_id": s["target_id"],
                "target_slug": s["target_slug"],
                "reason": s["reason"],
                "score": s["score"]
            })
            
        # Save results
        count = 0
        for dev_id, sugs in grouped.items():
            delegate.save_suggestions(dev_id, sugs)
            count += len(sugs)
            
        # Rebuild master index to reflect new suggestions
        from python_worker.developer_index import rebuild_master_index
        rebuild_master_index(dev_dir)
        
        duration = time.time() - start_t
        logger.info(f"Manual similarity analysis finished in {duration:.2f}s. Generated {count} suggestions.")
        
    except Exception as e:
        logger.error(f"Manual similarity analysis failed: {e}", exc_info=True)

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
        """
        Pobiera dane wszystkich deweloperów bezpośrednio z indeksu (O(1) Disk I/O).
        Indeks zawiera już wszystkie dane potrzebne do algorytmów podobieństwa:
        - nazwy, slugi, relacje (parent/master)
        - podsumowanie inwestycji (slugi + koordynaty)
        """
        from python_worker import developer_index
        start_t = time.time()
        
        try:
            # Pobieramy zunifikowane dane z 'hot indexu'
            devs = developer_index.load(self.dev_dir)
            if not devs:
                logger.warning("get_developers_for_analysis: Index empty or missing.")
                return []

            logger.info(
                f"[PERF] Similarity analysis scan: Loaded {len(devs)} developers from index "
                f"in {time.time() - start_t:.3f}s (Zero Disk I/O)"
            )
            return devs
            
        except Exception as e:
            logger.error(f"Failed to load developers for analysis: {e}", exc_info=True)
            return []

    def get_dismissed_cache(self) -> dict[str, set[str]]:
        return _build_dismissed_cache(self.dev_dir)

    def save_suggestions(self, dev_id: str, suggestions: list[dict]):
        fresh_dev = self.dm.get_developer_by_id(dev_id)
        if fresh_dev:
            # Map input suggestions to our storage format
            new_suggestions_map = {}
            for s in suggestions:
                new_suggestions_map[s["target_id"]] = {
                    "usi_dev_id": s["target_id"],
                    "developer_slug": s["target_slug"],
                    "reason": s["reason"],
                    "score": s["score"]
                }

            # Merge with existing (preserve existing, update with new if better)
            existing = fresh_dev.get("suggestions", [])
            existing_map = {s["usi_dev_id"]: s for s in existing}
            
            # DIRTY CHECK: Only proceed with save if we actually have NEW or BETTER suggestions
            has_changes = False
            for target_id, new_s in new_suggestions_map.items():
                if target_id not in existing_map:
                    has_changes = True
                    existing_map[target_id] = new_s
                elif new_s["score"] > existing_map[target_id].get("score", 0):
                    has_changes = True
                    existing_map[target_id] = new_s

            if has_changes:
                fresh_dev["suggestions"] = list(existing_map.values())
                self.dm.create_developer_file(fresh_dev)
                logger.info(f"[IO_SAVE] Updated suggestions for {dev_id} (found new or improved matches).")

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
            "get_scraper_config": get_shared_config,
            "parse_url": parse_url,
            "log_to_dev_log": log_to_dev_log
        }
        _crawler_instance = WedrowiecDaemon(context)
    return _crawler_instance

def get_crawler():
    return _crawler_instance
