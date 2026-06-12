import sys
import logging
import json
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")
from python_worker.config import get_scraper_config
from python_worker.services.scraper_gateway import ScraperGateway
from usi_scrapers.scraper_otodom import discover_otodom_listing
from usi_scrapers.fetcher import Fetcher

logging.basicConfig(level=logging.DEBUG)
config = get_scraper_config()
fetcher = Fetcher(config)
url = "https://www.otodom.pl/pl/firmy/deweloperzy/deweloper-ID10556292?limit=72&currentPage=1"
items = discover_otodom_listing(config, fetcher, url, limit=None, pagination_param="currentPage")
print(f"Items found: {len(items)}")
# Print first item ID just to see what it is
if items:
    print(f"First item: {items[0]}")
