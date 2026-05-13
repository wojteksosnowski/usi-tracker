
import json
import logging
from pathlib import Path
from python_worker.services.investment_service import InvestmentService
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("RepairScript")

def repair_local_data():
    svc = InvestmentService()
    data_dir = Path(USI_DATA_DIR)
    
    # 1. Find all usi_*.json files
    usi_files = list(data_dir.glob("**/usi_*.json"))
    logger.info(f"Found {len(usi_files)} total investment records.")
    
    repaired_count = 0
    errors_count = 0
    verified_count = 0
    
    for usi_path in usi_files:
        try:
            with open(usi_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check if repair is needed
            needs_dev = not data.get("developer")
            needs_price = data.get("financials", {}).get("price_min") is None or data.get("financials", {}).get("price_min") == 0
            
            if needs_dev or needs_price:
                dev_slug = data.get("developer_slug")
                inv_slug = data.get("investment_slug")
                
                if not dev_slug or not inv_slug:
                    # Try to infer from path
                    inv_slug = usi_path.stem.replace("usi_", "")
                    dev_slug = usi_path.parent.parent.name
                
                logger.info(f"Repairing {dev_slug}/{inv_slug}...")
                
                # Perform local update
                success = svc.update_investment(dev_slug, inv_slug, use_local_raw=True)
                
                if success:
                    repaired_count += 1
                    # Immediate validation
                    with open(usi_path, "r", encoding="utf-8") as f:
                        updated_data = json.load(f)
                    
                    # Check metadata
                    has_dev = bool(updated_data.get("developer"))
                    has_price = updated_data.get("financials", {}).get("price_min") is not None
                    
                    # Check images
                    image_paths = updated_data.get("image_paths", [])
                    valid_images = True
                    for p in image_paths:
                        # Path is like /Public/USI/dev/inv/file.jpg
                        # We need to map it to local disk
                        local_p = Path(PUBLIC_USI_DIR).parent / p.lstrip("/")
                        if not local_p.exists():
                            # Fallback check relative to PUBLIC_USI_DIR if it starts with /Public/USI/
                            if p.startswith("/Public/USI/"):
                                rel_p = p.replace("/Public/USI/", "")
                                local_p = Path(PUBLIC_USI_DIR) / rel_p
                                
                        if not local_p.exists():
                            logger.warning(f"  [IMG MISSING] {p} -> {local_p}")
                            valid_images = False
                    
                    if has_dev and valid_images:
                        verified_count += 1
                    else:
                        logger.warning(f"  [REPAIR INCOMPLETE] dev:{has_dev}, price:{has_price}, images:{valid_images}")
                else:
                    logger.warning(f"  [SKIPPED] No local raw data for {dev_slug}/{inv_slug}")
            
        except Exception as e:
            logger.error(f"  [ERROR] {usi_path}: {e}")
            errors_count += 1

    logger.info("--- Repair Summary ---")
    logger.info(f"Total processed: {len(usi_files)}")
    logger.info(f"Successfully repaired: {repaired_count}")
    logger.info(f"Verified (Dev + Images): {verified_count}")
    logger.info(f"Errors: {errors_count}")

if __name__ == "__main__":
    repair_local_data()
