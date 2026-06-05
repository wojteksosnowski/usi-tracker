import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import json
import logging
from python_worker.services.investment_service import InvestmentService
from python_worker.config import USI_DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("backfill_distances")

def main():
    service = InvestmentService()
    sync_service = service.sync
    
    data_dir = Path(USI_DATA_DIR)
    
    # Force index load
    import python_worker.investment_index as inv_index
    all_invs = inv_index.get_index(data_dir)
    logger.info(f"Loaded {len(all_invs)} investments from index.")
    
    updated = 0
    total = len(all_invs)
    
    for i, inv_entry in enumerate(all_invs):
        inv_id = inv_entry.get("usi_inv_id")
        if not inv_id: 
            continue
        
        if i > 0 and i % 500 == 0:
            logger.info(f"Progress: {i}/{total} ({round(i/total*100, 1)}%)")
            
        coords = inv_entry.get("coords")
        if not coords or coords[0] is None or coords[0] == 0:
            continue
            
        # Calculate nearby
        nearby = sync_service._calculate_nearby_investments(inv_id, coords)
        
        # Load full JSON and update
        try:
            resources = service.get_investment_resources(inv_id)
            if not resources or not resources["files"].get("anchor"):
                continue
                
            anchor_path = resources["files"]["anchor"]
            with open(anchor_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["nearby_investments"] = nearby
            
            with open(anchor_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            updated += 1
        except Exception as e:
            logger.error(f"Failed to update {inv_id}: {e}")

    logger.info(f"Finished. Updated {updated} investments.")

if __name__ == "__main__":
    main()
