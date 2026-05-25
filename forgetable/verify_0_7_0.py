import sys
import logging
import json
import shutil
import tempfile
from pathlib import Path
from usi_scrapers import api as scraper_api
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Verify070")

def test_saving_logic():
    temp_root = Path(tempfile.mkdtemp(prefix="usi_v070_"))
    try:
        config = get_scraper_config()
        config.public_dir = temp_root
        
        # Ensure directories exist
        (temp_root / "USIdata").mkdir()
        (temp_root / "USIdev").mkdir()
        (temp_root / "USI").mkdir()
        
        fetcher = Fetcher(config)
        
        # Test Investment Saving
        portal = "rp"
        inv_id = "20322"
        dev_slug = "ekopark"
        inv_slug = "forma-otwarta"
        
        logger.info(f"Testing investment saving for {portal}...")
        # fetch_investment DOES NOT SAVE. download_raw does.
        raw_path = scraper_api.download_raw(config, fetcher, portal, inv_id, dev_slug, inv_slug)
        
        if not raw_path or not raw_path.exists():
            logger.error(f"Investment raw file missing or not returned. Got: {raw_path}")
            # Try to find it elsewhere to see where it was saved
            all_files = list(temp_root.glob("**/*.json"))
            logger.info(f"Found files: {[str(f.relative_to(temp_root)) for f in all_files]}")
            return False
            
        logger.info(f"✅ Investment raw file saved at {raw_path.relative_to(temp_root)}")

        # Test Developer Saving
        logger.info(f"Testing developer saving for {portal}...")
        # Get dev_id from the saved file to be sure
        with open(raw_path, 'r') as f:
            data = json.load(f)
            dev_id = data.get("vendor", {}).get("id")
            
        if not dev_id:
            logger.error("Could not find developer ID in raw file")
            return False

        # save_raw_developer expects portal_id as a separate argument in v0.7.0 (api.py:397)
        dev_raw_path = scraper_api.save_raw_developer(config, data.get("vendor", {}), dev_slug, portal, portal_id=str(dev_id))

        
        if not dev_raw_path or not dev_raw_path.exists():
            logger.error("Failed to save developer raw file")
            return False
            
        logger.info(f"✅ Developer raw file saved at {dev_raw_path.relative_to(temp_root)}")
        
        return True
    finally:
        shutil.rmtree(temp_root)
        logger.info("Cleaned up temp directory")

if __name__ == "__main__":
    if test_saving_logic():
        logger.info("🚀 VERSION 0.7.0 SAVING LOGIC VERIFIED")
        sys.exit(0)
    else:
        logger.error("❌ VERSION 0.7.0 SAVING LOGIC FAILED")
        sys.exit(1)
