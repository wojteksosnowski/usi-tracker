import sys
import logging
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
from usi_scrapers import api as scraper_api
from usi_scrapers.fetcher import Fetcher
from python_worker.adapters import AdapterFactory
from python_worker.config import get_scraper_config
from python_worker.slug_utils import slugify

# Configure logging to be concise
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("IngestionCheck")

# Configuration of "Gold Standard" URLs for testing
TEST_CASES = {
    "rp": {
        "name": "RynekPierwotny",
        "url": "https://rynekpierwotny.pl/oferty/ekopark/forma-otwarta-etap-c-krakow-pradnik-bialy-20322/",
        "id": "20322",
        "dev_slug": "ekopark",
        "inv_slug": "forma-otwarta-etap-c-krakow-pradnik-bialy",
        "adapter_key": "rp"
    },
    "oto": {
        "name": "Otodom",
        "url": "https://www.otodom.pl/pl/inwestycja/poczatek-polnocy-ID4mYvY",
        "id": "https://www.otodom.pl/pl/inwestycja/poczatek-polnocy-ID4mYvY", # API expects URL for oto
        "dev_slug": "yit-development",
        "inv_slug": "poczatek-polnocy",
        "adapter_key": "oto"
    },
    "to": {
        "name": "TabelaOfert",
        "url": "https://tabelaofert.pl/inwestycja/nowe-kolibki,i7332",
        "id": "https://tabelaofert.pl/inwestycja/nowe-kolibki,i7332",
        "dev_slug": "invest-komfort",
        "inv_slug": "nowe-kolibki",
        "adapter_key": "to"
    }
}

def check_portal(portal_key, temp_data_dir, temp_assets_dir):
    test = TEST_CASES.get(portal_key)
    if not test:
        logger.error(f"Unknown portal: {portal_key}")
        return False

    logger.info(f"--- Testing {test['name']} (ISOLATED) ---")
    logger.info(f"URL: {test['url']}")

    config = get_scraper_config()
    # Patch the config to use temporary directory for assets
    config.public_dir = temp_root
    fetcher = Fetcher(config)
    
    try:
        # 1. Scrape (Network via library API)
        res = scraper_api.fetch_investment(
            config, fetcher, portal_key, test["id"]
        )

        if not res or "error" in res:
            logger.error(f"Scrape failed: {res.get('error') if res else 'Empty response'}")
            return False

        raw_details = res.get("raw_details")
        if not raw_details:
            logger.error("No raw_details in scrape result")
            return False

        # 2. Adapt (Data Transformation via Tracker Factory)
        adapter = AdapterFactory.get_adapter(test["adapter_key"])
        unified = adapter.transform(raw_details, test["inv_slug"], test["dev_slug"])
        
        # 3. Save Images (via library TechnicalDataManager to simulate full flow)
        from usi_scrapers.manager import TechnicalDataManager
        tm = TechnicalDataManager(config)
        
        all_urls = res.get("image_urls", [])
        if all_urls:
            saved = tm.sync_images(all_urls, test["dev_slug"], test["inv_slug"])
            logger.info(f"Saved {len([f for f in saved if f])} images to {temp_assets_dir}")

        # 4. Validate Critical Fields
        errors = []
        
        # Identity
        if unified.get("investment_slug") != test["inv_slug"]:
            errors.append(f"Slug mismatch: expected {test['inv_slug']}, got {unified.get('investment_slug')}")
        
        if not unified.get("name"):
            errors.append("Missing investment name")
            
        if not unified.get("developer") or slugify(unified.get("developer")) == "nieznany-deweloper":
            errors.append(f"Invalid developer: {unified.get('developer')}")

        # Location
        loc = unified.get("location", {})
        coords = loc.get("coords", [])
        if not coords or len(coords) < 2 or not all(coords):
            errors.append(f"Missing or invalid coordinates: {coords}")
        
        if not loc.get("city"):
            errors.append("Missing city")
            
        if not loc.get("address"):
            errors.append("Missing address")

        # Media - Check if files actually exist in TEMP directory
        img_dir = temp_assets_dir / test["dev_slug"] / test["inv_slug"]
        if not img_dir.exists() or len(list(img_dir.glob("*"))) == 0:
            errors.append(f"Images not found in temp directory: {img_dir}")

        if not unified.get("image_urls") or len(unified.get("image_urls")) == 0:
            errors.append("No source image URLs found in adapted data")

        if errors:
            for err in errors:
                logger.error(f"FAIL: {err}")
            return False

        logger.info(f"✅ {test['name']} Ingestion OK (Verified in isolation)")
        logger.info(f"   Name: {unified.get('name')}")
        logger.info(f"   Dev:  {unified.get('developer')}")
        logger.info(f"   Loc:  {loc.get('city')}, {loc.get('district') or 'N/A'}")
        logger.info(f"   Img:  {len(list(img_dir.glob('*')))} files found in TEMP")
        return True

    except Exception as e:
        logger.exception(f"Critical error testing {test['name']}: {e}")
        return False

if __name__ == "__main__":
    requested_portals = sys.argv[1:] if len(sys.argv) > 1 else ["rp", "oto", "to"]
    
    # Setup temporary environment
    temp_root = Path(tempfile.mkdtemp(prefix="usi_test_"))
    temp_data = temp_root / "USIdata"
    temp_assets = temp_root / "USI"
    temp_data.mkdir()
    temp_assets.mkdir()
    
    logger.info(f"🚀 Starting isolated ingestion tests in: {temp_root}")
    
    try:
        overall_success = True
        for p in requested_portals:
            # Cleanup for current key (some shells pass --portal all)
            if p.startswith("--"): continue
            if not check_portal(p, temp_data, temp_assets):
                overall_success = False
                
        if not overall_success:
            logger.error("❌ Some ingestion tests FAILED")
            sys.exit(1)
        else:
            logger.info("🎉 ALL INGESTION TESTS PASSED IN ISOLATION")
            sys.exit(0)
    finally:
        # Cleanup
        shutil.rmtree(temp_root)
        logger.info(f"🧹 Cleaned up temporary directory: {temp_root}")

if __name__ == "__main__":
    portals = sys.argv[1:] if len(sys.argv) > 1 else ["rp", "oto", "to"]
    
    # Setup temporary environment
    temp_root = Path(tempfile.mkdtemp(prefix="usi_test_"))
    temp_data = temp_root / "USIdata"
    temp_assets = temp_root / "USI"
    temp_data.mkdir()
    temp_assets.mkdir()
    
    logger.info(f"🚀 Starting isolated ingestion tests in: {temp_root}")
    
    try:
        overall_success = True
        for p in portals:
            if not check_portal(p, temp_data, temp_assets):
                overall_success = False
                
        if not overall_success:
            logger.error("❌ Some ingestion tests FAILED")
            sys.exit(1)
        else:
            logger.info("🎉 ALL INGESTION TESTS PASSED IN ISOLATION")
            sys.exit(0)
    finally:
        # Cleanup
        shutil.rmtree(temp_root)
        logger.info(f"🧹 Cleaned up temporary directory: {temp_root}")
