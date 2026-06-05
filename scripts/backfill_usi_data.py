import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.config import USI_DATA_DIR
from python_worker.services.investment_loader import load_investment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill")

def main():
    data_dir = Path(USI_DATA_DIR)
    
    # Find all usi_*.json files
    usi_files = list(data_dir.rglob("usi_*.json"))
    logger.info(f"Found {len(usi_files)} usi_*.json files to backfill.")
    
    success = 0
    errors = 0
    
    for usi_file in usi_files:
        try:
            # Load using the current volatile loader which computes everything on the fly
            inv_data = load_investment(usi_file=usi_file, data_dir=data_dir)
            if not inv_data:
                logger.warning(f"Could not load data for {usi_file}")
                errors += 1
                continue
                
            # Now we want to update the original usi_*.json with the computed fields
            original_data = json.loads(usi_file.read_text())
            
            # Fields to backfill
            fields_to_sync = [
                "photos", "amenities_score", "amenities_matched", 
                "suggested_udogodnienia", "ratings", "comment", 
                "photos_to_delete"
            ]
            
            changed = False
            for field in fields_to_sync:
                if field in inv_data:
                    original_data[field] = inv_data[field]
                    changed = True
                    
            if changed:
                # Save back to usi_*.json
                usi_file.write_text(json.dumps(original_data, ensure_ascii=False, indent=2))
                success += 1
                
        except Exception as e:
            logger.error(f"Error processing {usi_file}: {e}")
            errors += 1
            
    logger.info(f"Backfill complete. Updated: {success}, Errors: {errors}")

if __name__ == "__main__":
    main()
