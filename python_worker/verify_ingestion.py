import sys
import logging
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
from python_worker.main import scrape_rynek_pierwotny, scrape_otodom, scrape_tabelaofert
from python_worker.adapters.rp import RPAdapter
from python_worker.adapters.otodom import OtodomAdapter
from python_worker.adapters.to import TOAdapter
from python_worker.csv_importer import slugify

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
        "adapter": RPAdapter
    },
    "oto": {
        "name": "Otodom",
        "url": "https://www.otodom.pl/pl/inwestycja/poczatek-polnocy-ID4mYvY",
        "id": "ID4mYvY",
        "dev_slug": "yit-development",
        "inv_slug": "poczatek-polnocy",
        "adapter": OtodomAdapter
    },
    "to": {
        "name": "TabelaOfert",
        "url": "https://tabelaofert.pl/inwestycja/nowe-kolibki,i7332",
        "id": "7332",
        "dev_slug": "invest-komfort",
        "inv_slug": "nowe-kolibki",
        "adapter": TOAdapter
    }
}

def check_portal(portal_key, temp_data_dir, temp_assets_dir):
    test = TEST_CASES.get(portal_key)
    if not test:
        logger.error(f"Unknown portal: {portal_key}")
        return False

    logger.info(f"--- Testing {test['name']} (ISOLATED) ---")
    logger.info(f"URL: {test['url']}")

    # Patch the config and its local imports to use temporary directories
    with patch("python_worker.config.USI_DATA_DIR", str(temp_data_dir)), \
         patch("python_worker.config.PUBLIC_USI_DIR", str(temp_assets_dir)), \
         patch("python_worker.image_saver.PUBLIC_USI_DIR", temp_assets_dir), \
         patch("python_worker.scraper_rp.USI_DATA_DIR", temp_data_dir):
        
        try:
            # 1. Scrape (Network + Raw Save to TEMP)
            if portal_key == "rp":
                res = scrape_rynek_pierwotny(test["id"], test["dev_slug"], test["inv_slug"], url=test["url"])
            elif portal_key == "oto":
                res = scrape_otodom(test["id"], test["dev_slug"], test["inv_slug"], url=test["url"])
            elif portal_key == "to":
                res = scrape_tabelaofert(test["id"], test["dev_slug"], test["inv_slug"], url=test["url"])

            if not res or "error" in res:
                logger.error(f"Scrape failed: {res.get('error') if res else 'Empty response'}")
                return False

            raw_details = res.get("raw_details")
            if not raw_details:
                logger.error("No raw_details in scrape result")
                return False

            # 2. Adapt (Data Transformation)
            unified = test["adapter"].transform(raw_details, test["inv_slug"], test["dev_slug"])
            
            # 3. Validate Critical Fields
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
            if not img_dir.exists() or len(list(img_dir.glob("*.jpg"))) == 0:
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
            logger.info(f"   Img:  {len(list(img_dir.glob('*.jpg')))} files found in TEMP")
            return True

        except Exception as e:
            logger.exception(f"Critical error testing {test['name']}: {e}")
            return False

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
