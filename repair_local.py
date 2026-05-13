
import json
import logging
from pathlib import Path
from python_worker.adapters import AdapterFactory, Merger
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("RepairScript")

def repair_local_strictly():
    data_dir = Path(USI_DATA_DIR)
    public_usi_dir = Path(PUBLIC_USI_DIR)
    
    usi_files = list(data_dir.glob("**/usi_*.json"))
    logger.info(f"Found {len(usi_files)} total investment records.")
    
    repaired_count = 0
    errors_count = 0
    verified_count = 0
    skipped_no_raw = 0
    
    for usi_path in usi_files:
        try:
            with open(usi_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check if repair is needed
            needs_dev = not data.get("developer")
            needs_price = data.get("financials", {}).get("price_min") is None or data.get("financials", {}).get("price_min") == 0
            
            if needs_dev or needs_price:
                inv_dir = usi_path.parent
                dev_slug = data.get("developer_slug") or inv_dir.parent.name
                inv_slug = data.get("investment_slug") or usi_path.stem.replace("usi_", "")
                
                # Try to find any raw file
                raw_files = list(inv_dir.glob("raw_*.json"))
                if not raw_files:
                    skipped_no_raw += 1
                    continue
                
                logger.info(f"Repairing {dev_slug}/{inv_slug}...")
                
                rp_unified = None
                oto_unified = None
                to_unified = None
                
                for rf in raw_files:
                    portal = None
                    if rf.name.startswith("raw_rp_"): portal = "rp"
                    elif rf.name.startswith("raw_oto_"): portal = "oto"
                    elif rf.name.startswith("raw_to_"): portal = "to"
                    
                    if portal:
                        try:
                            with open(rf, "r", encoding="utf-8") as f:
                                raw_data = json.load(f)
                            # Passing slugs for consistency
                            unified = AdapterFactory.get_adapter(portal).transform(raw_data, inv_slug, dev_slug)
                            if portal == "rp": rp_unified = unified
                            elif portal == "oto": oto_unified = unified
                            elif portal == "to": to_unified = unified
                        except Exception as e:
                            logger.error(f"  Error processing {rf.name}: {e}")

                if rp_unified or oto_unified or to_unified:
                    # Merge with existing data
                    new_unified = Merger.merge(
                        rp_data=rp_unified, 
                        oto_data=oto_unified, 
                        to_data=to_unified, 
                        existing_data=data, 
                        event="Local Rebuild (Repair)"
                    )
                    
                    # Validate metadata
                    has_dev = bool(new_unified.get("developer"))
                    has_price = new_unified.get("financials", {}).get("price_min") is not None
                    
                    # Validate images (ONLY check if they exist, do NOT sync/download)
                    image_paths = new_unified.get("image_paths", [])
                    if not image_paths:
                        # If image_paths empty, scan disk
                        img_dir = public_usi_dir / dev_slug / inv_slug
                        if img_dir.is_dir():
                            on_disk = sorted(p.name for p in img_dir.iterdir() 
                                            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
                            if on_disk:
                                new_unified["image_paths"] = [f"/Public/USI/{dev_slug}/{inv_slug}/{fname}" for fname in on_disk]
                                new_unified["images_count"] = len(on_disk)
                                image_paths = new_unified["image_paths"]

                    valid_images = True
                    missing_images = []
                    for p in image_paths:
                        # Normalize path for checking
                        rel_path = p.replace("/Public/USI/", "")
                        local_p = public_usi_dir / rel_path
                        if not local_p.exists():
                            valid_images = False
                            missing_images.append(p)
                    
                    # Save repaired record
                    with open(usi_path, "w", encoding="utf-8") as f:
                        json.dump(new_unified, f, indent=2, ensure_ascii=False)
                    
                    repaired_count += 1
                    
                    if has_dev and has_price and valid_images and image_paths:
                        verified_count += 1
                    else:
                        issues = []
                        if not has_dev: issues.append("missing dev")
                        if not has_price: issues.append("missing price")
                        if not image_paths: issues.append("no images")
                        if not valid_images: issues.append(f"missing {len(missing_images)} files")
                        logger.warning(f"  [INCOMPLETE] {dev_slug}/{inv_slug}: {', '.join(issues)}")
                else:
                    logger.warning(f"  [FAILED] Could not transform raw data for {dev_slug}/{inv_slug}")
            
        except Exception as e:
            logger.error(f"  [ERROR] {usi_path}: {e}")
            errors_count += 1

    logger.info("--- Strictly Local Repair Summary ---")
    logger.info(f"Total investment files: {len(usi_files)}")
    logger.info(f"Skipped (no raw files): {skipped_no_raw}")
    logger.info(f"Successfully repaired: {repaired_count}")
    logger.info(f"Verified (Dev + Price + Images): {verified_count}")
    logger.info(f"Errors during processing: {errors_count}")

if __name__ == "__main__":
    repair_local_strictly()
