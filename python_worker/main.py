import argparse
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

from .config import USI_DATA_DIR, USI_DEV_DIR
from .adapters import RPAdapter, OtodomAdapter, TOAdapter, Merger
from .scraper_rp import scrape_rynek_pierwotny, discover_rp_investments, download_raw_rp_json, download_raw_rp_dev_json
from .scraper_otodom import scrape_otodom, discover_otodom_investments, download_raw_otodom_json, download_raw_otodom_dev_json
from .scraper_to import scrape_tabelaofert, discover_to_investments, download_raw_to_json, download_raw_to_dev_json
from .csv_importer import import_csv
from .logger_utils import log_to_processing_log
from .developer_manager import DeveloperManager

# Set up logging for the whole application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/worker.log")
    ]
)
logger = logging.getLogger("USIWorker")

def download_raw_json(portal: str, identifier: str, dev_slug: str, inv_slug: str) -> Path | None:
    """Helper to route raw download to the correct scraper."""
    if portal == "rp":
        return download_raw_rp_json(identifier, dev_slug, inv_slug)
    elif portal == "oto" or portal == "otodom":
        return download_raw_otodom_json(identifier, dev_slug, inv_slug)
    elif portal == "to":
        return download_raw_to_json(identifier, dev_slug, inv_slug)
    return None

def process_discovery_queue(items: list[dict], portal: str, dev_slug: str):
    """
    Downloads raw JSONs for a list of discovered items.
    """
    from .portal_matcher import filter_new_investments
    # Only download for net-new items
    portal_key = "rp" if portal == "rp" else ("otodom" if portal == "oto" else "to")
    filtered = filter_new_investments(items, portal_key)
    new_items = [item for item in filtered if item.get("is_new")]
    
    if not new_items:
        logger.info(f"No new items to download for {portal} ({dev_slug})")
        return

    logger.info(f"Downloading raw JSONs for {len(new_items)} new items on {portal}...")
    for item in new_items:
        inv_slug = item.get("slug")
        identifier = item.get("id") or item.get("url")
        if not inv_slug or not identifier:
            continue
            
        try:
            download_raw_json(portal, identifier, dev_slug, inv_slug)
        except Exception as e:
            logger.error(f"Failed to download raw JSON for {inv_slug}: {e}")

def update_developer_profile(dev_slug: str):
    """
    Fetches and saves raw developer profile JSONs from all configured portals.
    """
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    dev_data = dm.get_developer(dev_slug)
    if not dev_data:
        logger.warning(f"Developer metadata not found for {dev_slug}, creating skeleton.")
        dev_data = {
            "developer_slug": dev_slug,
            "name": dev_slug.replace("-", " ").title(),
            "portal_mapping": {"rp": None, "oto": None, "to": None}
        }

    mapping = dev_data.get("portal_mapping", {})
    
    # RP
    rp_map = mapping.get("rp") or {}
    rp_id = rp_map.get("id") or rp_map.get("slug")
    if rp_id:
        logger.info(f"Downloading raw RP profile for {dev_slug} (ID: {rp_id})")
        download_raw_rp_dev_json(rp_id, dev_slug)
    
    # Otodom
    oto_map = mapping.get("oto") or {}
    oto_url = oto_map.get("url")
    if oto_url:
        logger.info(f"Downloading raw Otodom profile for {dev_slug} (URL: {oto_url})")
        download_raw_otodom_dev_json(oto_url, dev_slug)

    # TabelaOfert
    to_map = mapping.get("to") or {}
    to_slug = to_map.get("slug")
    if to_slug:
        to_url = f"https://tabelaofert.pl/katalog-firm/deweloperzy/{to_slug}"
        logger.info(f"Downloading raw TO profile for {dev_slug} (URL: {to_url})")
        download_raw_to_dev_json(to_url, dev_slug)

def backfill_usi_ids():
    """
    Scans all developers and investments, assigning missing usi_dev_id and usi_inv_id.
    """
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    
    # 1. Backfill Developers
    logger.info("Backfilling developer IDs...")
    dev_count = 0
    dev_map = {} # slug -> usi_dev_id
    
    for dev_file in USI_DEV_DIR.glob("usi_dev_*.json"):
        try:
            with open(dev_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            updated = False
            if "usi_dev_id" not in data:
                data["usi_dev_id"] = dm.generate_usi_id("DEV")
                updated = True
            
            dev_map[data["developer_slug"]] = data["usi_dev_id"]
            
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
            if "usi_inv_id" not in data:
                data["usi_inv_id"] = dm.generate_usi_id("INV")
                updated = True
            
            # Ensure usi_dev_id is present if developer_slug matches
            dev_slug = data.get("developer_slug")
            if dev_slug and dev_slug in dev_map:
                if data.get("usi_dev_id") != dev_map[dev_slug]:
                    data["usi_dev_id"] = dev_map[dev_slug]
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
    service = InvestmentService()
    return service.update_investment(dev_slug, inv_slug, use_local_raw=use_local_raw)

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

    # Command: migrate
    parser_migrate = subparsers.add_parser("migrate", help="Run the full database migration (legacy)")
    parser_migrate.add_argument("--limit", type=int, help="Limit number of investments")

    # Command: discover
    parser_discover = subparsers.add_parser("discover", help="Discover new investments for a developer")
    parser_discover.add_argument("dev_slug", help="Developer slug")
    parser_discover.add_argument("--download", action="store_true", help="Download raw JSONs for new investments")

    # Command: download-raw
    parser_dl = subparsers.add_parser("download-raw", help="Download raw JSON for an investment")
    parser_dl.add_argument("inv_path", help="Investment path (dev_slug/inv_slug)")
    parser_dl.add_argument("--portal", choices=["rp", "oto", "to"], help="Force specific portal")

    # Command: rebuild-from-raw
    parser_rb = subparsers.add_parser("rebuild-from-raw", help="Rebuild usi_*.json from local raw_*.json files")
    parser_rb.add_argument("inv_path", help="Investment path (dev_slug/inv_slug)")

    # Command: import-csv
    parser_import_csv = subparsers.add_parser("import-csv", help="Import investments from USImaster.csv")
    parser_import_csv.add_argument("--csv", default="reference-data/coda/USImaster.csv", help="Path to CSV file")
    parser_import_csv.add_argument("--limit", type=int, help="Limit number of rows to process")
    parser_import_csv.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser_import_csv.add_argument("--no-split", action="store_true", help="Do not split dual RP+OTO records")

    # Command: backfill-ids
    parser_backfill = subparsers.add_parser("backfill-ids", help="Generate and assign missing USI IDs for all records")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
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
        
        if update_investment(dev_slug, inv_slug):
            logger.info(f"Successfully updated {args.inv_path}")
        else:
            logger.error(f"Failed to update {args.inv_path}")

    elif args.command == "download-raw":
        logger.info(f"Downloading raw JSON for: {args.inv_path}")
        try:
            dev_slug, inv_slug = args.inv_path.split("/")
        except ValueError:
            logger.error("Investment path must be in format dev_slug/inv_slug")
            sys.exit(1)
            
        inv_dir = USI_DATA_DIR / dev_slug / inv_slug
        usi_file = inv_dir / f"usi_{inv_slug}.json"
        if not usi_file.exists():
            logger.error(f"Investment info not found: {usi_file}")
            sys.exit(1)
            
        with open(usi_file, "r") as f:
            data = json.load(f)
            sources = data.get("sources", {})
            
        success = False
        portals_to_try = ["rp", "oto", "to"] if not args.portal else [args.portal]
        for p in portals_to_try:
            if p in sources:
                identifier = sources[p].get("id") or sources[p].get("url")
                if identifier:
                    if download_raw_json(p, identifier, dev_slug, inv_slug):
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
        
        dev_dir = USI_DATA_DIR / args.dev_slug
        dev_json = dev_dir / f"usi_dev_{args.dev_slug}.json"
        
        if not dev_json.exists():
            logger.error(f"Developer info not found: {dev_json}")
            sys.exit(1)
            
        with open(dev_json, "r", encoding="utf-8") as f:
            dev_data = json.load(f)
            
        portal_mapping = dev_data.get("portal_mapping", {})
        
        # Get existing investment IDs/URLs
        existing_rp_ids = set()
        existing_oto_urls = set()
        
        for inv_dir in dev_dir.iterdir():
            if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                usi_file = inv_dir / f"usi_{inv_dir.name}.json"
                if usi_file.exists():
                    with open(usi_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sources = data.get("sources", {})
                        if "rp" in sources and sources["rp"].get("id"):
                            existing_rp_ids.add(str(sources["rp"]["id"]))
                        if "oto" in sources and sources["oto"].get("url"):
                            existing_oto_urls.add(sources["oto"]["url"])
                            
        # Discover RynekPierwotny
        rp_id = portal_mapping.get("rp", {}).get("id")
        if rp_id:
            logger.info(f"Checking RynekPierwotny (ID: {rp_id})...")
            new_rp = discover_rp_investments(rp_id)
            logger.info(f"Found {len(new_rp)} investments on RynekPierwotny.")
            for inv in new_rp:
                if inv["id"] not in existing_rp_ids:
                    logger.info(f"REGISTERING NEW RP Investment: {inv['name']} (ID: {inv['id']}, Slug: {inv['slug']})")
                    inv_slug = inv["slug"]
                    new_inv_dir = dev_dir / inv_slug
                    new_inv_dir.mkdir(parents=True, exist_ok=True)
                    skeleton = {
                        "investment_slug": inv_slug,
                        "developer_slug": args.dev_slug,
                        "name": inv["name"],
                        "sources": {"rp": {"id": inv["id"]}},
                        "audit": {"created_at": datetime.now().isoformat()}
                    }
                    with open(new_inv_dir / f"usi_{inv_slug}.json", "w", encoding="utf-8") as f:
                        json.dump(skeleton, f, indent=2, ensure_ascii=False)
                    log_to_processing_log(args.dev_slug, inv_slug, f"Discovered and registered from RynekPierwotny (ID: {inv['id']})")
            
            if args.download:
                process_discovery_queue(new_rp, "rp", args.dev_slug)
        
        # Discover Otodom
        oto_agency_ids = portal_mapping.get("oto", {}).get("agency_ids", [])
        if not oto_agency_ids and portal_mapping.get("oto", {}).get("agency_id"):
            oto_agency_ids = [portal_mapping["oto"]["agency_id"]]
            
        for agency_id in oto_agency_ids:
            logger.info(f"Checking Otodom (Agency ID: {agency_id})...")
            new_oto = discover_otodom_investments(str(agency_id))
            logger.info(f"Found {len(new_oto)} potential offers on Otodom.")
            for inv in new_oto:
                if inv["url"] not in existing_oto_urls:
                    logger.info(f"REGISTERING NEW Otodom Investment: {inv['name']} (URL: {inv['url']})")
                    inv_slug = inv["slug"]
                    new_inv_dir = dev_dir / inv_slug
                    new_inv_dir.mkdir(parents=True, exist_ok=True)
                    skeleton = {
                        "investment_slug": inv_slug,
                        "developer_slug": args.dev_slug,
                        "name": inv["name"],
                        "sources": {"oto": {"url": inv["url"]}},
                        "audit": {"created_at": datetime.now().isoformat()}
                    }
                    with open(new_inv_dir / f"usi_{inv_slug}.json", "w", encoding="utf-8") as f:
                        json.dump(skeleton, f, indent=2, ensure_ascii=False)
                    log_to_processing_log(args.dev_slug, inv_slug, f"Discovered and registered from Otodom (URL: {inv['url']})")
            
            if args.download:
                process_discovery_queue(new_oto, "oto", args.dev_slug)
        
        # Discover TabelaOfert
        to_mapping = portal_mapping.get("to", {})
        to_id = to_mapping.get("agency_id") or to_mapping.get("slug")
        if to_id:
            logger.info(f"Checking TabelaOfert (Identifier: {to_id})...")
            new_to = discover_to_investments(str(to_id))
            logger.info(f"Found {len(new_to)} investments on TabelaOfert.")
            # Get existing TO URLs for this developer to avoid duplicates
            existing_to_urls = set()
            for inv_dir in dev_dir.iterdir():
                if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                    usi_file = inv_dir / f"usi_{inv_dir.name}.json"
                    if usi_file.exists():
                        with open(usi_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if "to" in data.get("sources", {}) and data["sources"]["to"].get("url"):
                                existing_to_urls.add(data["sources"]["to"]["url"])

            for inv in new_to:
                if inv["url"] not in existing_to_urls:
                    logger.info(f"REGISTERING NEW TO Investment: {inv['name']} (URL: {inv['url']})")
                    inv_slug = inv["slug"]
                    new_inv_dir = dev_dir / inv_slug
                    new_inv_dir.mkdir(parents=True, exist_ok=True)
                    skeleton = {
                        "investment_slug": inv_slug,
                        "developer_slug": args.dev_slug,
                        "name": inv["name"],
                        "sources": {"to": {"url": inv["url"]}},
                        "audit": {"created_at": datetime.now().isoformat()}
                    }
                    with open(new_inv_dir / f"usi_{inv_slug}.json", "w", encoding="utf-8") as f:
                        json.dump(skeleton, f, indent=2, ensure_ascii=False)
                    log_to_processing_log(args.dev_slug, inv_slug, f"Discovered and registered from TabelaOfert (URL: {inv['url']})")
            
            if args.download:
                for inv in new_to:
                    download_raw_json("to", inv["url"], args.dev_slug, inv["slug"])

        logger.info("Discovery finished.")

    elif args.command == "import-csv":
        logger.info(f"Starting CSV import from: {args.csv}")
        import_csv(
            csv_path=args.csv,
            output_dir=USI_DATA_DIR,
            limit=args.limit,
            dry_run=args.dry_run,
            split_dual=not args.no_split
        )
        logger.info("CSV import finished.")

    elif args.command == "backfill-ids":
        backfill_usi_ids()

if __name__ == "__main__":
    main()
