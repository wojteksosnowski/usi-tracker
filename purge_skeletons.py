
import json
import shutil
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("CleanupScript")

def purge_skeletons():
    data_dir = Path(USI_DATA_DIR)
    public_usi_dir = Path(PUBLIC_USI_DIR)
    
    usi_files = list(data_dir.glob("**/usi_*.json"))
    logger.info(f"Scanning {len(usi_files)} investment records for skeletons...")
    
    purged_count = 0
    
    for usi_path in usi_files:
        if usi_path.name.startswith("usi_dev_"):
            continue
            
        inv_dir = usi_path.parent
        raw_files = list(inv_dir.glob("raw_*.json"))
        
        # Skeleton is defined as having NO raw files
        if not raw_files:
            logger.info(f"Purging skeleton: {inv_dir}")
            
            # 1. Remove from USIdata
            try:
                shutil.rmtree(inv_dir)
            except Exception as e:
                logger.error(f"Failed to remove data dir {inv_dir}: {e}")
                
            # 2. Remove from USI assets (if exists)
            # Map USIdata path to USI assets path
            # USIdata/{dev}/{inv} -> USI/{dev}/{inv}
            rel_path = inv_dir.relative_to(data_dir)
            asset_dir = public_usi_dir / rel_path
            if asset_dir.exists():
                try:
                    shutil.rmtree(asset_dir)
                except Exception as e:
                    logger.error(f"Failed to remove asset dir {asset_dir}: {e}")
            
            purged_count += 1

    logger.info(f"Cleanup complete. Purged {purged_count} skeleton records.")

if __name__ == "__main__":
    purge_skeletons()
