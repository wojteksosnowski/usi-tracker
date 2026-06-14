import json
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR, get_shared_scraper_gateway

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    gateway = get_shared_scraper_gateway()
    base_dir = Path(USI_DATA_DIR)
    
    fixed_count = 0
    scanned_count = 0
    
    # Iterate through developer/investment dirs
    for dev_dir in base_dir.iterdir():
        if not dev_dir.is_dir() or dev_dir.name in ["reports", "index"]: continue
        
        for inv_dir in dev_dir.iterdir():
            if not inv_dir.is_dir(): continue
            
            for file_path in inv_dir.glob("usi_oto_*.json"):
                scanned_count += 1
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        usi_data = json.load(f)
                    
                    portal_id = usi_data.get("sources", {}).get("oto", {}).get("id")
                    if not portal_id:
                        continue
                        
                    raw_path = inv_dir / f"raw_oto_{portal_id}.json"
                    if not raw_path.exists():
                        continue
                        
                    with open(raw_path, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                    
                    from usi_scrapers.mapping import transform_to_unified
                    unified = transform_to_unified("oto", raw_data)
                    new_dev_name = unified.get("developer_name")
                    current_dev_name = usi_data.get("developer")
                    
                    if new_dev_name and current_dev_name != new_dev_name:
                        logger.info(f"[{inv_dir.name}] Correcting developer: '{current_dev_name}' -> '{new_dev_name}'")
                        usi_data["developer"] = new_dev_name
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(usi_data, f, ensure_ascii=False, indent=2)
                        fixed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    
    logger.info(f"Finished! Scanned: {scanned_count}, Fixed: {fixed_count}.")

if __name__ == "__main__":
    main()
