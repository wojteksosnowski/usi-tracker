import json
import logging
import argparse
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from usi_scrapers.mapping import get_mapping, resolve_path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def migrate_investment(usi_path: Path, dry_run: bool = True):
    try:
        data = json.loads(usi_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load {usi_path}: {e}")
        return

    sources = data.get("sources", {})
    if not sources:
        logger.warning(f"No sources in {usi_path.name}")
        return

    # Assuming one portal per anchor file (based on USIdata structure)
    portal = list(sources.keys())[0]
    portal_id = sources[portal].get("id")
    
    if not portal_id:
        logger.warning(f"Could not resolve ID for {usi_path.name}")
        return

    # Extract metadata...
    meta = {
        "status": data.get("status", "Brak"),
        "reviewed": data.get("reviewed", False),
        "issue_reports": data.get("issue_reports", []),
        "website": data.get("website"),
        "ratings": data.get("ratings", {}),
        "audit": data.get("audit", {})
    }
    
    # Define filenames using resolved portal_id
    raw_file_name = f"raw_{portal}_{portal_id}.json"
    meta_file_name = f"meta_{portal}_{portal_id}.json"

    # Define Anchor
    anchor = {
        "usi_inv_id": data.get("usi_inv_id"),
        "portal": portal,
        "portal_id": portal_id,
        "raw_file": raw_file_name,
        "meta_file": meta_file_name,
        "master_id": data.get("master_id"),
        "last_updated": data.get("last_updated_ts")
    }

    if dry_run:
        logger.info(f"[DRY-RUN] Would migrate {usi_path.name} to {anchor['portal_id']}")
    else:
        parent = usi_path.parent
        (parent / meta_file_name).write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        (parent / f"usi_{portal}_{portal_id}.json").write_text(json.dumps(anchor, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--subset", type=str, help="dev slug to migrate")
    args = parser.parse_args()

    pattern = f"{args.subset}/" if args.subset else "**/";
    logger.info(f"Scanning {USI_DATA_DIR} with pattern {pattern}...")
    
    for usi_file in USI_DATA_DIR.rglob(f"{pattern}usi_*.json"):
        if "usi_dev_" in usi_file.name or "usi_counters" in usi_file.name: continue
        migrate_investment(usi_file, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
