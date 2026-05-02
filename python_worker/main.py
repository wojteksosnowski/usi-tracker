import argparse
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

from .config import USI_DATA_DIR
from .adapters import RPAdapter, OtodomAdapter, TOAdapter, Merger
from .scraper_rp import scrape_rynek_pierwotny, discover_rp_investments, download_raw_rp_json
from .scraper_otodom import scrape_otodom, discover_otodom_investments, download_raw_otodom_json
from .scraper_to import scrape_tabelaofert, discover_to_investments, download_raw_to_json
from .csv_importer import import_csv
from .logger_utils import log_to_processing_log

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

def update_investment(dev_slug, inv_slug, use_local_raw=False):
    inv_dir = USI_DATA_DIR / dev_slug / inv_slug
    usi_path = inv_dir / f"usi_{inv_slug}.json"

    if not usi_path.exists() and not use_local_raw:
        logger.warning(f"Investment file not found skipping: {usi_path}")
        return False

    usi_data = {}
    if usi_path.exists():
        with open(usi_path, "r", encoding="utf-8") as f:
            usi_data = json.load(f)

    sources = usi_data.get("sources", {})
    # If no usi file but we want to use local raw, we need to infer sources or rely on existing raw files
    if not sources and use_local_raw:
        # Try to infer from raw files
        for p in ["rp", "oto", "to"]:
            raw_path = inv_dir / f"raw_{p}_{inv_slug}.json"
            if raw_path.exists():
                sources[p] = {"id": "rebuild"} # Placeholder

    rp_unified = None
    oto_unified = None
    to_unified = None
    fetched_sources = []

    # Update RynekPierwotny
    if "rp" in sources:
        raw_rp_path = inv_dir / f"raw_rp_{inv_slug}.json"
        if use_local_raw and raw_rp_path.exists():
            with open(raw_rp_path, "r") as f:
                raw_details = json.load(f)
                rp_unified = RPAdapter.transform(raw_details, inv_slug, dev_slug)
                fetched_sources.append("RP (local)")
        elif sources["rp"].get("id"):
            offer_id = sources["rp"]["id"]
            logger.info(f"Scraping RynekPierwotny for ID: {offer_id}")
            rp_result = scrape_rynek_pierwotny(offer_id, dev_slug, inv_slug)
            if "raw_details" in rp_result:
                from .developer_manager import DeveloperManager
                dm = DeveloperManager(USI_DATA_DIR)
                dm.save_raw_json(rp_result["raw_details"], dev_slug, inv_slug, "rp")
                rp_unified = RPAdapter.transform(rp_result["raw_details"], inv_slug, dev_slug)
                fetched_sources.append("RP")

    # Update Otodom
    if "oto" in sources:
        raw_oto_path = inv_dir / f"raw_oto_{inv_slug}.json"
        if use_local_raw and raw_oto_path.exists():
            with open(raw_oto_path, "r") as f:
                raw_details = json.load(f)
                oto_unified = OtodomAdapter.transform(raw_details, inv_slug, dev_slug)
                fetched_sources.append("Otodom (local)")
        elif sources["oto"].get("url"):
            oto_url = sources["oto"]["url"]
            logger.info(f"Scraping Otodom for URL: {oto_url}")
            oto_result = scrape_otodom(oto_url, dev_slug, inv_slug)
            if "raw_details" in oto_result:
                from .developer_manager import DeveloperManager
                dm = DeveloperManager(USI_DATA_DIR)
                dm.save_raw_json(oto_result["raw_details"], dev_slug, inv_slug, "oto")
                oto_unified = OtodomAdapter.transform(oto_result["raw_details"], inv_slug, dev_slug)
                fetched_sources.append("Otodom")

    # Update TabelaOfert
    if "to" in sources:
        raw_to_path = inv_dir / f"raw_to_{inv_slug}.json"
        if use_local_raw and raw_to_path.exists():
            with open(raw_to_path, "r") as f:
                raw_details = json.load(f)
                to_unified = TOAdapter.transform(raw_details, inv_slug, dev_slug)
                fetched_sources.append("TO (local)")
        elif sources["to"].get("url"):
            to_url = sources["to"]["url"]
            logger.info(f"Scraping TabelaOfert for URL: {to_url}")
            to_result = scrape_tabelaofert(to_url, dev_slug, inv_slug)
            if "raw_details" in to_result:
                from .developer_manager import DeveloperManager
                dm = DeveloperManager(USI_DATA_DIR)
                dm.save_raw_json(to_result["raw_details"], dev_slug, inv_slug, "to")
                to_unified = TOAdapter.transform(to_result["raw_details"], inv_slug, dev_slug)
                fetched_sources.append("TO")

    # Merge
    if rp_unified or oto_unified or to_unified:
        ratings_path = inv_dir / f"meta_{inv_slug}_ratings.json"
        ratings = {}
        if ratings_path.exists():
            with open(ratings_path, "r", encoding="utf-8") as f:
                ratings = json.load(f)
        
        event = f"Sync: {', '.join(fetched_sources)}" if fetched_sources else "Manual Update"
        new_unified = Merger.merge(rp_unified, oto_unified, to_unified, ratings, existing_data=usi_data, event=event)
        
        # Ensure images are downloaded if we have URLs and no paths
        all_urls = new_unified.get("image_urls", [])
        if all_urls:
            from .image_saver import save_images
            logger.info(f"Checking images for {inv_slug} ({len(all_urls)} URLs)")
            saved = save_images(all_urls, dev_slug, inv_slug)
            new_unified["image_paths"] = [f"/Public/USI/{dev_slug}/{inv_slug}/{fname}" for fname in saved]
            new_unified["images_count"] = len(saved)

        with open(usi_path, "w", encoding="utf-8") as f_out:
            json.dump(new_unified, f_out, indent=2, ensure_ascii=False)
        
        log_to_processing_log(dev_slug, inv_slug, f"Updated investment data. Sources: {', '.join(fetched_sources)}")
        logger.info(f"Successfully updated {usi_path}")
        return True
    
    return False

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
        dev_dir = USI_DATA_DIR / args.dev_slug
        if not dev_dir.exists():
            logger.error(f"Developer directory not found: {dev_dir}")
            sys.exit(1)
        
        # Iterate over all investment folders
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

if __name__ == "__main__":
    main()
