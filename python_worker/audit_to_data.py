"""
audit_to_data.py — Audit and repair tool for TabelaOfert (TO) developers and investments.
"""
import json
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime

from python_worker.config import USI_DATA_DIR, USI_DEV_DIR, get_scraper_config
from python_worker.developer_manager import DeveloperManager
from python_worker.adapters import PORTAL_MAPPING
from usi_scrapers import resolve_path
from python_worker.url_parser import parse_url
from usi_scrapers import api as scraper_api
from usi_scrapers.fetcher import Fetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def audit_to_data(repair=False):
    data_dir = Path(USI_DATA_DIR)
    dev_dir = Path(USI_DEV_DIR)
    dm = DeveloperManager(data_dir, dev_dir)
    
    lib_config = get_scraper_config()
    fetcher = Fetcher(lib_config) if lib_config else None
    
    stats = {
        "devs_checked": 0,
        "devs_with_to": 0,
        "devs_missing_logo": 0,
        "devs_missing_raw": 0,
        "logos_downloaded": 0,
        "invs_checked": 0,
        "invs_with_to": 0,
        "invs_missing_id": 0,
        "invs_ids_fixed": 0,
        "invs_missing_raw": 0
    }

    logger.info("=== Starting TabelaOfert Audit ===")

    # 1. Audit Developers
    for dev_subdir in dev_dir.iterdir():
        if not dev_subdir.is_dir(): continue
        
        usi_files = list(dev_subdir.glob("usi_dev_*.json"))
        for usi_file in usi_files:
            stats["devs_checked"] += 1
            try:
                with open(usi_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                pm = data.get("portal_mapping", {})
                if not pm or not pm.get("to"):
                    # Check if it has raw_to_*.json anyway (incomplete Level 2)
                    if any(dev_subdir.glob("raw_to_*.json")):
                        logger.info(f"Developer {dev_subdir.name} has raw TO files but no Level 2 mapping.")
                    else:
                        continue
                
                stats["devs_with_to"] += 1
                dev_slug = data["developer_slug"]
                
                # Check for logo
                has_logo = any(dev_subdir.glob("logo.*"))
                
                # Normalize legacy logo names (e.g. logo_to_atal.webp -> logo.webp)
                if not has_logo:
                    legacy_logos = list(dev_subdir.glob("logo_*.*"))
                    if legacy_logos:
                        legacy = legacy_logos[0]
                        target = dev_subdir / f"logo{legacy.suffix}"
                        logger.info(f"Normalizing logo name: {legacy.name} -> {target.name}")
                        if repair:
                            legacy.rename(target)
                            has_logo = True

                if not has_logo:
                    stats["devs_missing_logo"] += 1
                    if repair and fetcher and lib_config:
                        # Try to find logo URL in raw files
                        logo_url = None
                        for raw_file in dev_subdir.glob("raw_to_*.json"):
                            try:
                                raw_data = json.load(raw_file.open(encoding="utf-8"))
                                to_cfg = PORTAL_MAPPING.get("to", {}).get("developer", {})
                                logo_url = resolve_path(raw_data, to_cfg.get("logo"))
                                if logo_url: break
                            except Exception: continue
                        
                        if logo_url:
                            logger.info(f"Downloading missing logo for {dev_slug} from {logo_url}")
                            try:
                                scraper_api.download_dev_logo(lib_config, fetcher, logo_url, dev_slug)
                                stats["logos_downloaded"] += 1
                            except Exception as e:
                                logger.error(f"Failed to download logo for {dev_slug}: {e}")

                # Check for raw files
                has_raw = any(dev_subdir.glob("raw_to_*.json"))
                if not has_raw:
                    stats["devs_missing_raw"] += 1
                    
                # Repair Level 2 if incomplete
                if repair and (not pm or not pm.get("to")) and has_raw:
                    logger.info(f"Repairing Level 2 mapping for {dev_slug}")
                    from python_worker.init_developers import _build_dev_from_raws
                    _build_dev_from_raws(dev_subdir, dev_slug, data.get("name"), dm)

            except Exception as e:
                logger.error(f"Error auditing developer {usi_file}: {e}")

    # 2. Audit Investments
    for inv_file in data_dir.rglob("usi_*.json"):
        if inv_file.name.startswith("usi_dev_"): continue
        stats["invs_checked"] += 1
        try:
            with open(inv_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            sources = data.get("sources", {})
            if "to" not in sources: continue
            
            stats["invs_with_to"] += 1
            to_src = sources["to"]
            
            # Check for ID
            if not to_src.get("id"):
                stats["invs_missing_id"] += 1
                url = to_src.get("url")
                if repair and url:
                    parsed = parse_url(url)
                    to_id = parsed.get("to_id")
                    if to_id:
                        logger.info(f"Fixing missing TO ID for {inv_file.parent.name}: {to_id}")
                        to_src["id"] = str(to_id)
                        data["audit"]["updated_at"] = datetime.now().isoformat()
                        with open(inv_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        stats["invs_ids_fixed"] += 1
            
            # Check for raw files
            has_raw = any(inv_file.parent.glob("raw_to_*.json"))
            if not has_raw:
                stats["invs_missing_raw"] += 1

        except Exception as e:
            logger.error(f"Error auditing investment {inv_file}: {e}")

    logger.info("=== Audit Summary ===")
    logger.info(f"Developers checked: {stats['devs_checked']}")
    logger.info(f"  - with TabelaOfert: {stats['devs_with_to']}")
    logger.info(f"  - missing logo:     {stats['devs_missing_logo']}")
    logger.info(f"  - missing raw:      {stats['devs_missing_raw']}")
    if repair:
        logger.info(f"  - logos downloaded: {stats['logos_downloaded']}")
    
    logger.info(f"Investments checked: {stats['invs_checked']}")
    logger.info(f"  - with TabelaOfert: {stats['invs_with_to']}")
    logger.info(f"  - missing technical ID: {stats['invs_missing_id']}")
    logger.info(f"  - missing raw:          {stats['invs_missing_raw']}")
    if repair:
        logger.info(f"  - IDs fixed:            {stats['invs_ids_fixed']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit and repair TabelaOfert data.")
    parser.add_argument("--repair", action="store_true", help="Perform automated repairs.")
    args = parser.parse_args()
    
    audit_to_data(repair=args.repair)
