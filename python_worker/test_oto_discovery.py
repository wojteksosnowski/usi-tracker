import logging
from python_worker.scraper_otodom import discover_otodom_listing
from python_worker.config import OTODOM_DISCOVERY_URLS
from python_worker.portal_matcher import filter_new_investments

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestOtoDiscovery")

def test_oto_discovery():
    logger.info("Starting Otodom discovery test (using centralized deduplication)...")
    
    url = OTODOM_DISCOVERY_URLS[0]
    discovered_items = discover_otodom_listing(url)
    
    if not discovered_items:
        logger.error("No items discovered. Check if Otodom structure changed or if blocked.")
        return

    logger.info(f"Discovered {len(discovered_items)} items from listing.")
    
    # Use centralized filtering
    filtered_items = filter_new_investments(discovered_items, "otodom")
    
    net_new = [item for item in filtered_items if item.get("is_new")]
    already_exists = [item for item in filtered_items if not item.get("is_new")]
            
    logger.info("=== Discovery Summary ===")
    logger.info(f"Total Discovered: {len(discovered_items)}")
    logger.info(f"Already in DB:   {len(already_exists)}")
    logger.info(f"Net New:         {len(net_new)}")
    logger.info("=========================")
    
    if net_new:
        logger.info("First 5 net-new items:")
        for item in net_new[:5]:
            logger.info(f" - {item['name']} | Developer: {item.get('developer') or 'Unknown'} ({item['url']})")

if __name__ == "__main__":
    test_oto_discovery()
