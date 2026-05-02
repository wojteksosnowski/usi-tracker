import time
import logging
from pathlib import Path
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestDbScan")

def test_performance():
    dm = DeveloperManager(USI_DATA_DIR)
    
    start_time = time.time()
    identifiers = dm.get_existing_identifiers()
    end_time = time.time()
    
    duration = end_time - start_time
    
    logger.info("=== Performance Results ===")
    logger.info(f"Total time: {duration:.4f} seconds")
    logger.info(f"RP IDs:     {len(identifiers['rp_ids'])}")
    logger.info(f"Oto IDs:    {len(identifiers['oto_ids'])}")
    logger.info(f"Oto Slugs:  {len(identifiers['oto_slugs'])}")
    logger.info("===========================")
    
    if duration > 2.0:
        logger.warning("Scan is slower than 2 seconds. Consider optimization if database grows significantly.")
    else:
        logger.info("Scan performance is excellent.")

if __name__ == "__main__":
    test_performance()
