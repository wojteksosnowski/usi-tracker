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
    from usi_crawlers.algorithms.similarity import normalize_name, calculate_similarities
    HAS_CRAWLERS = True
except ImportError:
    HAS_CRAWLERS = False

logger = logging.getLogger(__name__)

def run_manual_doktor_analysis(data_dir: Path, dev_dir: Path):
    """Performs a one-off similarity analysis and saves results without a daemon."""
    if not HAS_CRAWLERS:
        logger.warning("run_manual_doktor_analysis: usi_crawlers not available.")
        return

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
        start_t = time.time()
        try:
            devs = self.dm.list_developers()
        except Exception as e:
            logger.critical(f"[FATAL] Failed to list developers from manager: {e}")
            return []

        logger.info(
            f"[CRITICAL_TRACE] Daemon: Starting full developer analysis scan. "
            f"Total developers to process: {len(devs)}"
        )
        processed = []

        for d in devs:
            slug = d.get("developer_slug")
            if not slug:
                continue
                
            norm = normalize_name(d["name"]) if HAS_CRAWLERS else d["name"]
            buckets = {}
            cities = set()

            dev_path = self.data_dir / slug

            logger.info(f"[CRITICAL_TRACE] Entering developer path for filesystem scan: {dev_path}")

            if not dev_path.exists():
                continue

            # Zabezpieczenie przed nieskończonym parsowaniem wadliwych struktur
            visited_dirs: set[Path] = set()
            
            try:
                sub_dirs = list(dev_path.iterdir())
            except Exception as e:
                logger.error(f"[IO_ERROR] Critical failure listing directory {dev_path}: {e}")
                # Dodaj minimalne opóźnienie, aby zapobiec zarzynaniu CPU w pętli nadrzędnej
                time.sleep(0.1)
                continue

            for inv_dir in sub_dirs:
                try:
                    real_path = inv_dir.resolve(strict=False) # Zmiana na strict=False zapobiega rzucaniu wyjątków przy braku pliku docelowego symlinka
                    if real_path in visited_dirs:
                        logger.warning(f"[CYCLE_DETECTED] Loop or duplicate detected: {inv_dir}. Skipping.")
                        continue
                    visited_dirs.add(real_path)
                except Exception as e:
                    logger.error(f"[IO_ERROR] Cannot resolve path bounds {inv_dir}: {e}")
                    continue

                if not inv_dir.is_dir() or inv_dir.name.startswith("."):
                    continue

                # Ograniczenie rglob/glob do czystego iterowania po konkretnym wzorcu
                try:
                    usi_files = [f for f in inv_dir.glob("usi_*.json") if "usi_dev_" not in f.name]
                except Exception as e:
                    logger.error(f"[IO_ERROR] Failed to glob files in {inv_dir}: {e}")
                    continue

                if not usi_files:
                    continue
                
                usi_file = usi_files[0]
                try:
                    with open(usi_file, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        coords = data.get("location", {}).get("coords")
                        city = data.get("location", {}).get("city")
                        if city:
                            cities.add(city.strip().lower())

                        specs = data.get("specifications", {})
                        year = specs.get("delivery_year")
                        quarter = specs.get("delivery_quarter")

                        if coords and len(coords) == 2:
                            lat, lon = coords
                            if lat == 0 and lon == 0:
                                continue

                            bkey = f"{round(lat, 2):.2f}_{round(lon, 2):.2f}"
                            if bkey not in buckets:
                                buckets[bkey] = []
                            buckets[bkey].append({
                                "lat": lat, "lon": lon,
                                "year": int(year) if year else None,
                                "quarter": int(quarter) if quarter else None
                            })
                except Exception as ex:
                    logger.error(f"[IO_ERROR] Failed to read or parse anchor file in {inv_dir}: {ex}")
                    continue

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

        duration = time.time() - start_t
        logger.info(
            f"[CRITICAL_TRACE] Daemon: Full developer analysis scan finished in "
            f"{duration:.2f}s (processed {len(processed)} developers)"
        )
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
            "get_scraper_config": get_shared_config,
            "parse_url": parse_url,
            "log_to_dev_log": log_to_dev_log
        }
        _crawler_instance = WedrowiecDaemon(context)
    return _crawler_instance

def get_crawler():
    return _crawler_instance
