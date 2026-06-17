import argparse
import sys
import os
import logging
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
import queue
import atexit

from .config import USI_DATA_DIR, USI_DEV_DIR, PUBLIC_USI_DIR, get_shared_config
from .adapters.merger import Merger
from usi_scrapers.fetcher import Fetcher
from usi_scrapers import api as scraper_api
from .logger_utils import log_to_processing_log
from .developer_manager import DeveloperManager
from .services.investment_service import InvestmentService

# Wymuś natychmiastowy zapis logów — krytyczne gdy proces działa za pipem
# (start-ui.sh), gdzie Python buforuje stdout/stderr w blokach 8 KB.
os.environ["PYTHONUNBUFFERED"] = "1"


class _Unbuffered:
    """Wymusza flush() po każdym write() na stdout/stderr."""
    __slots__ = ("_stream",)

    def __init__(self, stream):
        self._stream = stream

    def write(self, data):
        self._stream.write(data)
        self._stream.flush()

    def writelines(self, lines):
        self._stream.writelines(lines)
        self._stream.flush()

    def __getattr__(self, attr):
        return getattr(self._stream, attr)


sys.stdout = _Unbuffered(sys.stdout)
sys.stderr = _Unbuffered(sys.stderr)

import time
import subprocess

def _get_git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).parent.parent, stderr=subprocess.DEVNULL).decode("utf-8").strip()
    except Exception:
        return "unknown"

_git_commit = _get_git_commit()
_session_id = int(time.time())

# Set up logging for the whole application
_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / f"worker_{_session_id}.log"
_formatter = logging.Formatter(f'%(asctime)s - [commit:{_git_commit}] - %(name)s - %(levelname)s - %(message)s')

_root = logging.getLogger()
_root.setLevel(logging.INFO)

# Czysty, standardowy FileHandler z buforowaniem (wątek tła zajmie się flushowaniem)
_file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(_formatter)

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)

# Implementacja asynchronicznej kolejki logów
_log_queue = queue.Queue(-1)
_queue_handler = QueueHandler(_log_queue)
_root.addHandler(_queue_handler)

# Listener przetwarza logi w osobnym wątku, nie blokując głównej pętli CPU
_listener = QueueListener(_log_queue, _stream_handler, _file_handler, respect_handler_level=True)
_listener.start()

# Rejestracja zatrzymania listenere przy wyjściu z aplikacji
atexit.register(_listener.stop)

logger = logging.getLogger("USIWorker")


# Global config and fetcher for library operations
lib_config = None
lib_fetcher = None

def get_lib_fetcher():
    global lib_config, lib_fetcher
    if lib_fetcher is None:
        lib_config = get_shared_config()
        if lib_config:
            lib_fetcher = Fetcher(lib_config)
    return lib_fetcher

def update_developer_profile(dev_slug: str):
    """
    Fetches and saves raw developer profile JSONs from all configured portals.
    """
    from .services.developer_service import DeveloperService
    svc = DeveloperService(USI_DATA_DIR, USI_DEV_DIR)
    svc.update_developer_profile(dev_slug)
def backfill_usi_ids():
    """
    Scans all developers and investments, assigning missing usi_dev_id and usi_inv_id.
    Strictly follows the ID-only rule, ignoring slugs for identity mapping.
    """
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    
    # 1. Backfill Developers
    logger.info("Backfilling developer IDs...")
    dev_count = 0
    # Mapping structure: portal -> portal_id -> usi_dev_id
    id_map = {
        "rp": {},  # vendor_id -> usi_dev_id
        "oto": {}, # agency_id -> usi_dev_id
        "to": {}   # developer_id -> usi_dev_id
    }
    
    # Use rglob to find files in subdirectories (new canonical structure)
    for dev_file in USI_DEV_DIR.rglob("usi_dev_*.json"):
        try:
            with open(dev_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            updated = False
            if "usi_dev_id" not in data:
                data["usi_dev_id"] = dm.generate_usi_id("DEV")
                updated = True
            
            dev_id = data["usi_dev_id"]
            pm = data.get("portal_mapping", {})
            
            # Map RP IDs
            rp_p = pm.get("rp") or {}
            rp_id = rp_p.get("id")
            if rp_id: id_map["rp"][str(rp_id)] = dev_id
            
            # Map Otodom IDs
            oto_p = pm.get("oto") or {}
            agency_ids = oto_p.get("agency_ids") or ([oto_p.get("agency_id")] if oto_p.get("agency_id") else [])
            for aid in agency_ids:
                if aid: id_map["oto"][str(aid)] = dev_id
                
            # Map TO IDs
            to_p = pm.get("to") or {}
            to_id = to_p.get("id")
            if to_id: id_map["to"][str(to_id)] = dev_id
            
            if updated:
                with open(dev_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                dev_count += 1
        except Exception as e:
            logger.error(f"Error backfilling developer {dev_file}: {e}")
            
    logger.info(f"Updated {dev_count} developer records with new USI IDs.")

    # 2. Backfill Investments
    logger.info("Backfilling investment IDs...")
    inv_count = 0
    for inv_file in USI_DATA_DIR.rglob("usi_*.json"):
        if inv_file.name.startswith("usi_dev_"):
            continue
            
        try:
            with open(inv_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            updated = False
            sources = data.get("sources", {})
            matched_dev_id = None
            
            # Attempt to find developer ID via portal IDs (ID-only priority)
            if "rp" in sources:
                vendor_id = sources["rp"].get("vendor_id")
                if vendor_id and str(vendor_id) in id_map["rp"]:
                    matched_dev_id = id_map["rp"][str(vendor_id)]
            
            if not matched_dev_id and "oto" in sources:
                agency_id = sources["oto"].get("agency_id")
                if agency_id and str(agency_id) in id_map["oto"]:
                    matched_dev_id = id_map["oto"][str(agency_id)]
                    
            if not matched_dev_id and "to" in sources:
                dev_id = sources["to"].get("developer_id")
                if dev_id and str(dev_id) in id_map["to"]:
                    matched_dev_id = id_map["to"][str(dev_id)]
            
            if matched_dev_id and data.get("usi_dev_id") != matched_dev_id:
                data["usi_dev_id"] = matched_dev_id
                updated = True
            
            # Backfill Investment ID (MANDATORY)
            if "usi_inv_id" not in data:
                data["usi_inv_id"] = dm.generate_usi_id("INV")
                updated = True
            
            if updated:
                with open(inv_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                inv_count += 1
        except Exception as e:
            logger.error(f"Error backfilling investment {inv_file}: {e}")
            
    logger.info(f"Updated {inv_count} investment records with new USI IDs.")

def update_investment(dev_slug, inv_slug, use_local_raw=False):
    from python_worker.services.investment_service import InvestmentService
    from python_worker.config import USI_DATA_DIR
    import json
    import logging
    service = InvestmentService()
    
    # Check if dev_slug is already a system_id
    if dev_slug.startswith("INV-"):
        return service.update_investment(dev_slug, use_local_raw=use_local_raw)
        
    # Resolve system_id from index
    index_path = USI_DATA_DIR / "_index.json"
    system_id = None
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
            for entry in index.get("entries", []):
                if entry.get("developer_slug") == dev_slug and entry.get("investment_slug") == inv_slug:
                    system_id = entry.get("usi_inv_id")
                    break
                    
    if not system_id:
        logging.getLogger(__name__).error(f"Could not find USI ID for {dev_slug}/{inv_slug} in index")
        return False
        
    return service.update_investment(system_id, use_local_raw=use_local_raw)

def main():
    parser = argparse.ArgumentParser(description="USI Tracker CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: ui
    parser_ui = subparsers.add_parser("ui", help="Start the local web interface")

    # Command: update-dev
    parser_update_dev = subparsers.add_parser("update-dev", help="Update all investments for a specific developer")
    parser_update_dev.add_argument("dev_slug", help="Developer slug (e.g., dom-development-sa)")

    # Command: update-inv
    parser_update_inv = subparsers.add_parser("update-inv", help="Update a specific investment")
    parser_update_inv.add_argument("inv_path", help="Investment path (e.g., dev_slug/inv_slug)")
    parser_update_inv.add_argument("--use-local-raw", action="store_true", help="Use local raw JSON if available")


    # Command: discover
    parser_discover = subparsers.add_parser("discover", help="Discover new investments for a developer")
    parser_discover.add_argument("dev_slug", help="Developer slug")
    parser_discover.add_argument("--download", action="store_true", help="Download raw JSONs for new investments")

    # Command: download-raw
    parser_dl = subparsers.add_parser("download-raw", help="Download raw JSON for an investment")
    parser_dl.add_argument("inv_path", help="Investment path (dev_slug/inv_slug)")
    parser_dl.add_argument("--portal", choices=["rp", "oto", "to"], help="Force specific portal")

    # Command: rebuild-from-raw
    parser_rebuild = subparsers.add_parser("rebuild-from-raw", help="Rebuild investment from local raw files")
    parser_rebuild.add_argument("inv_path", help="Investment path (e.g., dev_slug/inv_slug)")
    parser_rebuild.add_argument("--use-local-raw", action="store_true", help="Use local raw JSON if available")

    # Command: backfill-ids
    parser_backfill = subparsers.add_parser("backfill-ids", help="Generate and assign missing USI IDs for all records")

    # Command: backfill-portals
    parser_bp = subparsers.add_parser("backfill-portals", help="Fill portal_mapping.rp/oto from Konkurenci.csv for existing dev files")
    parser_bp.add_argument("--csv", default="reference-data/coda/Konkurenci.csv", help="Path to Konkurenci.csv")
    parser_bp.add_argument("--dry-run", action="store_true", help="Show what would be updated without writing")

    # Command: init-devs
    parser_init_devs = subparsers.add_parser("init-devs", help="Initialize developers from Konkurenci.csv")
    parser_init_devs.add_argument("--csv", help="Path to Konkurenci.csv", default="reference-data/coda/Konkurenci.csv")
    parser_init_devs.add_argument("--dry-run", action="store_true", help="Dry run without writing files")

    # Command: rebuild-devs
    parser_rebuild_devs = subparsers.add_parser("rebuild-devs", help="Build usi_dev_*.json from raw files for all USIdev directories")
    parser_rebuild_devs.add_argument("--force", action="store_true", help="Rebuild even if usi_dev_*.json already exists")
    parser_rebuild_devs.add_argument("--dry-run", action="store_true", help="Show what would be built without writing")

    # Command: rebuild-all
    parser_rebuild_all = subparsers.add_parser("rebuild-all", help="Build usi_*.json from local raw files for every investment in USIdata")
    parser_rebuild_all.add_argument("--force", action="store_true", help="Rebuild even if usi_*.json already exists")

    # Command: suggest
    parser_suggest = subparsers.add_parser("suggest", help="Run the developer suggestion algorithm (similarity & location)")

    # Command: suggest-invs
    parser_suggest_invs = subparsers.add_parser("suggest-invs", help="Run the investment suggestion algorithm")
    parser_suggest_invs.add_argument("--dev", type=str, help="Developer slug to scan within")
    parser_suggest_invs.add_argument("--inv", type=str, help="Specific investment USI ID to scan for")


    # Command: rebuild-index
    subparsers.add_parser("rebuild-index", help="Rebuild the investment list index (_index.json in USIdata)")

    # Command: rebuild-dev-index
    subparsers.add_parser("rebuild-dev-index", help="Rebuild the developer list index (_dev_index.json in USIdev)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command in ["daemon-wedrowiec", "daemon-doktor"]:
        print("[CRITICAL] Commands related to Wędrowiec and Doktor daemons are deprecated and removed.")
        sys.exit(1)

    if args.command == "ui":
        logger.info("Starting UI server...")
        from .ui_server import run as run_ui
        run_ui()
        
    elif args.command == "update-dev":
        logger.info(f"Starting update for developer: {args.dev_slug}")
        
        # 1. Update developer profile (raw JSONs)
        update_developer_profile(args.dev_slug)
        
        dev_dir = USI_DATA_DIR / args.dev_slug
        if not dev_dir.exists():
            logger.error(f"Developer directory not found: {dev_dir}")
            sys.exit(1)
        
        # 2. Iterate over all investment folders
        updated_count = 0
        for inv_dir in dev_dir.iterdir():
            if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                inv_slug = inv_dir.name
                if update_investment(args.dev_slug, inv_slug):
                    updated_count += 1
        
        logger.info(f"Finished update for developer {args.dev_slug}. Updated {updated_count} investments.")
        
    elif args.command == "update-inv":
        logger.info(f"Starting update for investment: {args.inv_path}")
        try:
            dev_slug, inv_slug = args.inv_path.split("/")
        except ValueError:
            logger.error("Investment path must be in format dev_slug/inv_slug")
            sys.exit(1)
        
        try:
            use_local_raw = getattr(args, "use_local_raw", False)
            if update_investment(dev_slug, inv_slug, use_local_raw=use_local_raw):
                logger.info(f"Successfully updated {args.inv_path}")
            else:
                logger.error(f"Failed to update {args.inv_path}")
        except Exception as e:
            logger.exception(f"Exception during update of {args.inv_path}")
            sys.exit(1)

    elif args.command == "download-raw":
        logger.info(f"Downloading raw JSON for: {args.inv_path}")
        try:
            dev_slug, inv_slug = args.inv_path.split("/")
        except ValueError:
            logger.error("Investment path must be in format dev_slug/inv_slug")
            sys.exit(1)
            
        # Resolve ID from slugs via index
        from .investment_index import load as load_index
        index = load_index(USI_DATA_DIR)
        entry = next((e for e in index if e.get("developer_slug") == dev_slug and e.get("investment_slug") == inv_slug), None)
        system_id = entry.get("usi_inv_id") if entry else None
        
        if not system_id:
            logger.error(f"Could not find USI ID for {args.inv_path} in index")
            sys.exit(1)
            
        svc = InvestmentService()
        resources = svc.get_investment_resources(system_id)
        if not resources or not resources["files"].get("anchor"):
            logger.error(f"Investment info not found for ID: {system_id}")
            sys.exit(1)
            
        with open(resources["files"]["anchor"], "r") as f:
            data = json.load(f)
            sources = data.get("sources", {})
            
        success = False
        portals_to_try = ["rp", "oto", "to"] if not args.portal else [args.portal]
        for p in portals_to_try:
            if p in sources:
                identifier = sources[p].get("id") or sources[p].get("url")
                if identifier:
                    if InvestmentService().download_raw_json(p, identifier, dev_slug, inv_slug):
                        success = True
        
        if success:
            logger.info("Raw download finished.")
        else:
            logger.error("No valid sources found for download.")

    elif args.command == "rebuild-from-raw":
        logger.info(f"Rebuilding {args.inv_path} from local raw files...")
        try:
            dev_slug, inv_slug = args.inv_path.split("/")
        except ValueError:
            logger.error("Investment path must be in format dev_slug/inv_slug")
            sys.exit(1)
            
        if update_investment(dev_slug, inv_slug, use_local_raw=True):
            logger.info(f"Successfully rebuilt {args.inv_path}")
        else:
            logger.error(f"Failed to rebuild {args.inv_path}. Ensure raw_*.json files exist.")

    elif args.command == "discover":
        logger.info(f"Discovering new investments for developer: {args.dev_slug}")
        from python_worker.services.discovery_service import DiscoveryService
        service = DiscoveryService()
        try:
            service.discover_for_developer(args.dev_slug, download=args.download)
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            sys.exit(1)
        logger.info("Discovery finished.")

    elif args.command == "backfill-ids":
        backfill_usi_ids()

    elif args.command == "backfill-portals":
        from .init_developers import backfill_from_konkurenci
        updated, skipped = backfill_from_konkurenci(
            konkurenci_path=Path(args.csv),
            dry_run=args.dry_run,
        )
        logger.info("backfill-portals done: %d updated, %d skipped", updated, skipped)

    elif args.command == "init-devs":
        logger.info(f"Initializing developers from: {args.csv}")
        from .init_developers import init_developers_from_konkurenci
        created, skipped = init_developers_from_konkurenci(
            konkurenci_path=Path(args.csv),
            dry_run=args.dry_run
        )
        logger.info(f"Developer initialization finished: {created} created, {skipped} skipped.")

    elif args.command == "rebuild-devs":
        logger.info("Rebuilding usi_dev_*.json from raw files...")
        from .init_developers import rebuild_devs_from_raws
        built = rebuild_devs_from_raws(USI_DEV_DIR, USI_DATA_DIR)
        logger.info(f"rebuild-devs finished: {built} built.")

    elif args.command == "rebuild-all":
        logger.info("Rebuilding usi_*.json from local raw files for all investments...")
        from .services.scraper_gateway import ScraperGateway
        from .investment_index import InvestmentIndex

        svc = InvestmentService()
        gateway = ScraperGateway()
        idx = InvestmentIndex(USI_DATA_DIR)
        
        all_investments = idx.get_all()
        built = failed = skipped = 0
        
        for entry in all_investments:
            system_id = entry.get("usi_inv_id")
            portal = entry.get("portal")
            portal_id = entry.get("portal_id")
            
            if not system_id or not portal or not portal_id:
                skipped += 1
                continue
                
            has_raw = gateway.has_local_raw(portal, str(portal_id))
            if not has_raw:
                skipped += 1
                continue

            # In force mode, we rebuild anyway. If not force, we would check if usi exists.
            # We can check if anchor file exists using identity.
            if not args.force:
                res = svc.identity.get_investment_resources(system_id)
                if res and res["files"].get("anchor"):
                    skipped += 1
                    continue

            try:
                ok = svc.update_investment(system_id, use_local_raw=True, skip_images=True, skip_index=True, skip_log=True)
                if ok:
                    built += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed {system_id}: {e}")
                failed += 1
                
            if built % 500 == 0 and built > 0:
                logger.info(f"Progress: {built} built, {failed} failed, {skipped} skipped...")
        logger.info(f"rebuild-all finished: {built} built, {failed} failed, {skipped} skipped.")

    elif args.command == "suggest":
        from python_worker.daemons import TrackerDoktorDelegate
        delegate = TrackerDoktorDelegate(USI_DATA_DIR, USI_DEV_DIR)
        try:
            from python_worker.algorithms.similarity.engine import calculate_similarities
            devs = delegate.get_developers_for_analysis()
            dismissed = delegate.get_dismissed_cache()
            suggestions = calculate_similarities(devs, dismissed)
            
            # Deduplicate by (source_id, target_id)
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
            for dev_id, sugs in grouped.items():
                delegate.save_suggestions(dev_id, sugs)
            logger.info(f"Suggestion algorithm finished. Found {len(unique_suggestions)} unique pairs.")
        except Exception as e:
            logger.error(f"Similarity algorithm failed: {e}")

    elif args.command == "suggest-invs":
        from .detect_similar_invs import detect_similar_invs
        detect_similar_invs(Path(USI_DATA_DIR), args.dev, args.inv)
        logger.info("Suggestion algorithm finished.")


    elif args.command == "rebuild-index":
        from .investment_index import rebuild as rebuild_index
        from .developer_index import rebuild as rebuild_dev_index, rebuild_master_index
        
        dev_dir = USI_DATA_DIR.parent / "USIdev"
        dev_index_file = dev_dir / "_dev_index.json"
        
        if not dev_index_file.exists():
            logger.info("Developer index missing. Rebuilding developer index first to ensure O(1) performance...")
            rebuild_master_index(dev_dir)
            rebuild_dev_index(USI_DATA_DIR, dev_dir)

        logger.info("Rebuilding investment index...")
        count = rebuild_index(USI_DATA_DIR, Path(PUBLIC_USI_DIR))
        logger.info(f"Done. {count} investments indexed.")

    elif args.command == "rebuild-dev-index":
        from .developer_index import rebuild as rebuild_dev_index, rebuild_master_index
        logger.info("Rebuilding developer index...")
        
        dev_dir = USI_DATA_DIR.parent / "USIdev"
        rebuild_master_index(dev_dir)
        count = rebuild_dev_index(USI_DATA_DIR, dev_dir)
        
        logger.info(f"Rebuilt index with {count} entries.")

if __name__ == "__main__":
    main()
