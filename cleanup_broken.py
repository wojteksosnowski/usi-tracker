
import json
import shutil
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("CleanupBroken")

def cleanup_broken_investments():
    data_dir = Path(USI_DATA_DIR)
    public_usi_dir = Path(PUBLIC_USI_DIR)
    
    # We scan all subdirectories {dev}/{inv}
    # find -mindepth 2 -maxdepth 2
    
    all_inv_dirs = []
    for dev_dir in data_dir.iterdir():
        if not dev_dir.is_dir():
            continue
        if dev_dir.name.startswith("."):
            continue
            
        for inv_dir in dev_dir.iterdir():
            if not inv_dir.is_dir():
                continue
            all_inv_dirs.append(inv_dir)
            
    logger.info(f"Scanning {len(all_inv_dirs)} investment directories...")
    
    deleted_count = 0
    
    for inv_dir in all_inv_dirs:
        files = list(inv_dir.iterdir())
        file_names = [f.name for f in files]
        
        # Filter out hidden files like .DS_Store
        real_files = [f for f in files if not f.name.startswith(".")]
        real_file_names = [f.name for f in real_files]
        
        is_broken = False
        reason = ""
        
        # Definition 1: No usi_*.json file
        usi_files = [n for n in real_file_names if n.startswith("usi_") and n.endswith(".json")]
        if not usi_files:
            is_broken = True
            reason = f"No usi_*.json found (files: {real_file_names})"
            
        # Definition 2: Skeletons (usi_*.json exists but it's a skeleton and no raw data)
        elif len(real_files) <= 2:
            # Check if it's a skeleton
            usi_path = inv_dir / usi_files[0]
            try:
                with open(usi_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # If status is "Brak" and no sources are filled or only skeleton sources
                if data.get("status") == "Brak" and not any(f.startswith("raw_") for f in real_file_names):
                    # Check assets
                    rel_path = inv_dir.relative_to(data_dir)
                    asset_dir = public_usi_dir / rel_path
                    has_assets = False
                    if asset_dir.exists():
                        asset_files = [f for f in asset_dir.iterdir() if not f.name.startswith(".")]
                        if asset_files:
                            has_assets = True
                    
                    if not has_assets:
                        is_broken = True
                        reason = f"Skeleton with no raw data and no assets (files: {real_file_names})"
            except Exception as e:
                logger.error(f"Error reading {usi_path}: {e}")
                # If it's unreadable, maybe it's broken too
                is_broken = True
                reason = f"Unreadable usi_*.json: {e}"

        if is_broken:
            logger.info(f"Deleting broken investment: {inv_dir} - Reason: {reason}")
            try:
                shutil.rmtree(inv_dir)
                
                # Also try to remove asset dir if it was empty or just had hidden files
                rel_path = inv_dir.relative_to(data_dir)
                asset_dir = public_usi_dir / rel_path
                if asset_dir.exists():
                    shutil.rmtree(asset_dir)
                    
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {inv_dir}: {e}")

    logger.info(f"Cleanup complete. Deleted {deleted_count} broken investment directories.")

if __name__ == "__main__":
    cleanup_broken_investments()
