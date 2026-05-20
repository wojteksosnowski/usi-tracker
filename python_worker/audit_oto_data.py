"""
audit_oto_data.py — Audit and repair tool for Otodom (OTO) developers and investments.
"""
import json
import logging
import argparse
import sys
import re
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

def audit_oto_data(repair=False):
    data_dir = Path(USI_DATA_DIR)
    dev_dir = Path(USI_DEV_DIR)
    dm = DeveloperManager(data_dir, dev_dir)
    
    lib_config = get_scraper_config()
    fetcher = Fetcher(lib_config) if lib_config else None
    
    stats = {
        "devs_checked": 0,
        "devs_with_oto": 0,
        "devs_missing_logo": 0,
        "devs_missing_raw": 0,
        "devs_missing_agency_id": 0,
        "devs_agency_ids_fixed": 0,
        "logos_downloaded": 0,
        "invs_checked": 0,
        "invs_with_oto": 0,
        "invs_missing_id": 0,
        "invs_ids_fixed": 0,
        "invs_missing_raw": 0
    }

    logger.info("=== Starting Otodom Audit ===")

    # 1. Audit Developers
    for dev_subdir in dev_dir.iterdir():
        if not dev_subdir.is_dir(): continue
        
        usi_files = list(dev_subdir.glob("usi_dev_*.json"))
        for usi_file in usi_files:
            stats["devs_checked"] += 1
            try:
                with open(usi_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                pm = data.get("portal_mapping") or {}
                oto_map = pm.get("oto")
                
                if not oto_map:
                    # Check if it has raw_oto_*.json anyway (incomplete Level 2)
                    if any(dev_subdir.glob("raw_oto_*.json")):
                        logger.info(f"Developer {dev_subdir.name} has raw OTO files but no Level 2 mapping.")
                        if repair:
                            logger.info(f"Repairing Level 2 mapping for {dev_slug}")
                            from python_worker.init_developers import _build_dev_from_raws
                            _build_dev_from_raws(dev_subdir, dev_slug, data.get("name"), dm)
                            # Reload data after repair
                            with open(usi_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            pm = data.get("portal_mapping") or {}
                            oto_map = pm.get("oto") or {}
                    else:
                        continue
                
                stats["devs_with_oto"] += 1
                dev_slug = data["developer_slug"]
                
                # Check for agency_id
                if not oto_map.get("agency_id"):
                    url = oto_map.get("url")
                    if url:
                        # Extract numeric agency_id from URL: .../deweloperzy/{slug}-ID{id}
                        m = re.search(r"-ID(\d+)$", url.rstrip("/"))
                        if m:
                            stats["devs_missing_agency_id"] += 1
                            agency_id = m.group(1)
                            if repair:
                                logger.info(f"Fixing missing Otodom agency_id for {dev_slug}: {agency_id}")
                                oto_map["agency_id"] = agency_id
                                data["audit"]["updated_at"] = datetime.now().isoformat()
                                with open(usi_file, "w", encoding="utf-8") as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                stats["devs_agency_ids_fixed"] += 1

                # Check for logo
                has_logo = any(dev_subdir.glob("logo.*"))
                if not has_logo:
                    stats["devs_missing_logo"] += 1
                    if repair and fetcher and lib_config:
                        # Try to find logo URL in raw files
                        logo_url = None
                        for raw_file in dev_subdir.glob("raw_oto_*.json"):
                            try:
                                raw_data = json.load(raw_file.open(encoding="utf-8"))
                                oto_cfg = PORTAL_MAPPING.get("oto", {}).get("developer", {})
                                logo_url = resolve_path(raw_data, oto_cfg.get("logo"))
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
                has_raw = any(dev_subdir.glob("raw_oto_*.json"))
                if not has_raw:
                    stats["devs_missing_raw"] += 1
                    
                # Repair Level 2 if incomplete
                if repair and (not pm or not pm.get("oto")) and has_raw:
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
            if "oto" not in sources: continue
            
            stats["invs_with_oto"] += 1
            oto_src = sources["oto"]
            
            # Check for ID
            if not oto_src.get("id"):
                stats["invs_missing_id"] += 1
                url = oto_src.get("url")
                if repair and url:
                    # Extract ID from URL
                    # Pattern 1: ...-ID([a-zA-Z0-9]+)$
                    m = re.search(r"-ID([a-zA-Z0-9]+)$", url.rstrip("/"))
                    if m:
                        oto_id = m.group(1)
                        logger.info(f"Fixing missing Otodom ID for {inv_file.parent.name}: {oto_id}")
                        oto_src["id"] = str(oto_id)
                        data["audit"]["updated_at"] = datetime.now().isoformat()
                        with open(inv_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        stats["invs_ids_fixed"] += 1
            
            # Check for raw files
            has_raw = any(inv_file.parent.glob("raw_oto_*.json"))
            if not has_raw:
                stats["invs_missing_raw"] += 1

        except Exception as e:
            logger.error(f"Error auditing investment {inv_file}: {e}")

    logger.info("=== Audit Summary ===")
    logger.info(f"Developers checked: {stats['devs_checked']}")
    logger.info(f"  - with Otodom:      {stats['devs_with_oto']}")
    logger.info(f"  - missing agency_id: {stats['devs_missing_agency_id']}")
    logger.info(f"  - missing logo:      {stats['devs_missing_logo']}")
    logger.info(f"  - missing raw:       {stats['devs_missing_raw']}")
    if repair:
        logger.info(f"  - agency_ids fixed:  {stats['devs_agency_ids_fixed']}")
        logger.info(f"  - logos downloaded:  {stats['logos_downloaded']}")
    
    logger.info(f"Investments checked: {stats['invs_checked']}")
    logger.info(f"  - with Otodom:         {stats['invs_with_oto']}")
    logger.info(f"  - missing technical ID: {stats['invs_missing_id']}")
    logger.info(f"  - missing raw:          {stats['invs_missing_raw']}")
    if repair:
        logger.info(f"  - IDs fixed:            {stats['invs_ids_fixed']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit and repair Otodom data.")
    parser.add_argument("--repair", action="store_true", help="Perform automated repairs.")
    args = parser.parse_args()
    
    audit_oto_data(repair=args.repair)
