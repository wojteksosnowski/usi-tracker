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
        "url": "https://www.otodom.pl/pl/inwestycja/wislane-tarasy-2-0-ID4lfZn",
        "dev_url": "https://www.otodom.pl/pl/firmy/deweloperzy/inter-bud-developer-ID9223014",
        "id": "https://www.otodom.pl/pl/inwestycja/wislane-tarasy-2-0-ID4lfZn",
        "dev_slug": "inter-bud-developer",
        "inv_slug": "wislane-tarasy-2-0",
        "adapter_key": "oto"
    },
    "to": {
        "name": "TabelaOfert",
        "url": "https://tabelaofert.pl/inwestycja/atal-aura-telefoniczna-21-lodz-srodmiescie-mieszkania-na-sprzedaz,i8975118",
        "id": "https://tabelaofert.pl/inwestycja/atal-aura-telefoniczna-21-lodz-srodmiescie-mieszkania-na-sprzedaz,i8975118",
        "dev_slug": "atal",
        "inv_slug": "atal-aura",
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
            target_image_dir = Path(temp_assets_dir) / test["dev_slug"] / test["inv_slug"]
            saved = tm.sync_images(all_urls, target_image_dir)
            logger.info(f"Saved {len([f for f in saved if f])} images to {target_image_dir}")

        # 4. Validate Critical Fields
        errors = []
        
        # Identity
        if unified.get("investment_slug") != test["inv_slug"]:
            errors.append(f"Slug mismatch: expected {test['inv_slug']}, got {unified.get('investment_slug')}")
        
        if not unified.get("name"):
            errors.append("Missing investment name")
            
        if not unified.get("developer") or unified.get("developer").lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper"):
            errors.append(f"Invalid developer: {unified.get('developer')}")

        # Location
        loc = unified.get("location", {})
        coords = loc.get("coords", [])
        if not coords or len(coords) < 2 or not all(coords):
            logger.warning(f"⚠️ Missing or invalid coordinates for {test['name']}: {coords}")
        
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
            logger.error(f"Validation failed for {test['name']}")
            logger.error(f"Unified Data: {json.dumps(unified, indent=2, ensure_ascii=False)}")
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

def check_developer(portal_key, temp_data_dir, temp_dev_dir):
    test = TEST_CASES.get(portal_key)
    logger.info(f"--- Testing {test['name']} DEVELOPER ---")
    
    config = get_scraper_config()
    config.public_dir = temp_root
    fetcher = Fetcher(config)
    
    try:
        # 1. Identify/Fetch Developer
        dev_name = None
        target_url = test.get("dev_url", test["url"])
        if portal_key in ("oto", "to"):
            dev_name = scraper_api.identify_developer(fetcher, portal_key, target_url)
        else:
            # For RP, we usually get dev info from listing or search
            # Here we just check if list_developers works
            page = scraper_api.list_developers(config, fetcher, portal_key, page=1)
            if page and page.developers:
                dev_name = page.developers[0].get("name")

        if not dev_name:
            logger.error(f"Could not identify developer for {portal_key}")
            return False
            
        logger.info(f"   Identified: {dev_name}")

        # 2. Save Raw Developer (L2 canonical check)
        # Mock some raw data to test saving according to portal_data_mapping
        portal_id = "test_id"
        if portal_key == "rp":
            mock_raw = {"vendor": {"id": portal_id}, "name": dev_name, "url": test["url"], "_is_test": True}
        elif portal_key == "oto":
            mock_raw = {"agency": {"id": portal_id}, "name": dev_name, "url": test["url"], "_is_test": True}
        elif portal_key == "to":
            mock_raw = {"brand": {"id": portal_id}, "name": dev_name, "url": test["url"], "_is_test": True}
        else:
            mock_raw = {"name": dev_name, "id": portal_id, "url": test["url"], "_is_test": True}

        raw_path = scraper_api.save_raw_developer(config, mock_raw, test["dev_slug"], portal_key, portal_id=portal_id)

        if not raw_path or not raw_path.exists():
            logger.error("Failed to save raw developer JSON")
            return False

        # Verify location according to canonical.md (L2: USIdev/{slug}/raw_{portal}_{id}.json)
        # Note: usi-scrapers v0.5.7+ uses ID if present in mock/data or passed as param
        # Here we check if the filename contains the ID
        expected_raw_name = f"raw_{portal_key}_{portal_id}.json"
        if raw_path.name != expected_raw_name:
             logger.error(f"Wrong raw filename: expected {expected_raw_name}, got {raw_path.name}")
             return False
        logger.info(f"✅ {test['name']} Developer Ingestion OK")
        logger.info(f"   Raw path: {raw_path.relative_to(temp_root)}")
        return True

    except Exception as e:
        logger.exception(f"Critical error testing {test['name']} developer: {e}")
        return False

if __name__ == "__main__":
    requested_portals = sys.argv[1:] if len(sys.argv) > 1 else ["rp", "oto", "to"]

    
    # Setup temporary environment
    temp_root = Path(tempfile.mkdtemp(prefix="usi_test_"))
    temp_data = temp_root / "USIdata"
    temp_dev = temp_root / "USIdev"
    temp_assets = temp_root / "USI"
    temp_data.mkdir()
    temp_dev.mkdir()
    temp_assets.mkdir()
    
    logger.info(f"🚀 Starting isolated ingestion tests in: {temp_root}")
    
    try:
        overall_success = True
        for p in requested_portals:
            if p.startswith("--") or p not in TEST_CASES: continue
            # Test Investment
            if not check_portal(p, temp_data, temp_assets):
                overall_success = False
            # Test Developer
            if not check_developer(p, temp_data, temp_dev):
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

