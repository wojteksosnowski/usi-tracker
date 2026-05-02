import json
import logging
from pathlib import Path
from python_worker.scraper_rp import discover_rp_investments
from python_worker.config import USI_DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RPDiscoveryTest")

def get_existing_rp_ids():
    existing_ids = set()
    for usi_file in USI_DATA_DIR.rglob("usi_*.json"):
        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                sources = data.get("sources", {})
                if "rp" in sources and sources["rp"].get("id"):
                    existing_ids.add(str(sources["rp"]["id"]))
        except Exception as e:
            logger.warning(f"Could not read {usi_file}: {e}")
    return existing_ids

def run_test():
    logger.info("Starting global RP discovery test (JSONMAIN)...")
    
    # Get discovered items
    discovered = discover_rp_investments()
    logger.info(f"Discovered {len(discovered)} items on RynekPierwotny.")
    
    # Get existing IDs
    existing_ids = get_existing_rp_ids()
    logger.info(f"Found {len(existing_ids)} existing RP investments in USIdata.")
    
    new_items = []
    already_known = 0
    stages_count = 0
    
    for item in discovered:
        if item.get("is_stage"):
            stages_count += 1
            
        if str(item["id"]) not in existing_ids:
            new_items.append(item)
        else:
            already_known += 1
            
    logger.info(f"--- Summary ---")
    logger.info(f"Total Discovered: {len(discovered)}")
    logger.info(f"Already Known:    {already_known}")
    logger.info(f"New Investments:  {len(new_items)}")
    logger.info(f"Stages Detected:  {stages_count}")
    
    if new_items:
        logger.info("--- New Items Preview (Top 5) ---")
        for item in new_items[:5]:
            stage_suffix = " [STAGE]" if item.get("is_stage") else ""
            logger.info(f"- {item['name']}{stage_suffix} (ID: {item['id']})")
            logger.info(f"  URL: {item['url']}")
    
    # Comparative check: if stages were detected, flattening is working
    if stages_count > 0:
        logger.info("SUCCESS: Stage-flattening confirmed.")
    else:
        logger.info("WARNING: No stages detected in this run. This might be normal if current listings have no stages.")

if __name__ == "__main__":
    run_test()
