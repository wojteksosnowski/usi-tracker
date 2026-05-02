import json
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_manager import DeveloperManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def migrate_developers():
    """
    Scans USI_DATA_DIR for unique developers and creates metadata files in USI_DEV_DIR.
    """
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    
    unique_devs = {} # slug -> name
    
    logger.info(f"Scanning {USI_DATA_DIR} for investments...")
    
    investment_files = list(USI_DATA_DIR.rglob("usi_*.json"))
    logger.info(f"Found {len(investment_files)} investment files.")
    
    for inv_file in investment_files:
        # Skip existing dev files if they were in the wrong place
        if inv_file.name.startswith("usi_dev_"):
            continue
            
        try:
            with open(inv_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            dev_slug = data.get("developer_slug")
            dev_name = data.get("developer")
            
            if dev_slug and dev_name:
                if dev_slug not in unique_devs:
                    unique_devs[dev_slug] = dev_name
                elif unique_devs[dev_slug] != dev_name:
                    # In case of name mismatch for same slug, we can log it but we keep the first one
                    # logger.warning(f"Name mismatch for {dev_slug}: '{unique_devs[dev_slug]}' vs '{dev_name}'")
                    pass
        except Exception as e:
            logger.error(f"Error reading {inv_file}: {e}")
            
    logger.info(f"Extracted {len(unique_devs)} unique developers.")
    
    created_count = 0
    updated_count = 0
    
    for dev_slug, dev_name in unique_devs.items():
        dev_file = USI_DEV_DIR / f"usi_dev_{dev_slug}.json"
        
        if dev_file.exists():
            # If exists, we might want to update the name if it's missing or something
            # but for now let's just count it
            updated_count += 1
            # We still call create_developer_file to update updated_at audit
        else:
            created_count += 1
            
        dev_data = {
            "developer_slug": dev_slug,
            "name": dev_name,
            "portal_mapping": {
                "rp": None,
                "oto": None,
                "to": None
            }
        }
        dm.create_developer_file(dev_data)
        
    logger.info(f"Migration complete: {created_count} new, {updated_count} updated.")

if __name__ == "__main__":
    migrate_developers()
