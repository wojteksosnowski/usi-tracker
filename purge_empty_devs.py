
import json
import shutil
import logging
from pathlib import Path
from python_worker.config import USI_DEV_DIR, USI_DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("PurgeDevs")

def purge_and_clear_suggestions():
    dev_dir = Path(USI_DEV_DIR)
    data_dir = Path(USI_DATA_DIR)
    
    dev_files = list(dev_dir.glob("usi_dev_*.json"))
    logger.info(f"Processing {len(dev_files)} developer files...")
    
    purged_count = 0
    cleared_count = 0
    
    for dev_path in dev_files:
        try:
            with open(dev_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            slug = data.get("developer_slug")
            if not slug:
                # Try to extract slug from filename
                slug = dev_path.stem.replace("usi_dev_", "")
            
            # Count investments
            inv_dir = data_dir / slug
            inv_count = 0
            if inv_dir.exists() and inv_dir.is_dir():
                # Count directories that have usi_*.json
                for sub in inv_dir.iterdir():
                    if sub.is_dir() and not sub.name.startswith("."):
                        if list(sub.glob("usi_*.json")):
                            inv_count += 1
            
            if inv_count == 0:
                logger.info(f"Purging empty developer: {slug}")
                dev_path.unlink()
                # Also check for discovery.json and other metadata in USIdev/{slug} folder if it exists
                # (though usually dev data is in usi_dev_{slug}.json, sometimes there is a folder too)
                dev_folder = dev_dir / slug
                if dev_folder.exists() and dev_folder.is_dir():
                    shutil.rmtree(dev_folder)
                purged_count += 1
            else:
                # Clear suggestions
                if "suggestions" in data:
                    data["suggestions"] = []
                    with open(dev_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    cleared_count += 1
                    
        except Exception as e:
            logger.error(f"Error processing {dev_path}: {e}")

    logger.info(f"Cleanup complete. Purged {purged_count} empty devs, cleared suggestions for {cleared_count} devs.")

if __name__ == "__main__":
    purge_and_clear_suggestions()
