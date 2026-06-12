import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")
from python_worker.config import get_scraper_config
from usi_scrapers.scraper_otodom import discover_otodom_investments
from usi_scrapers.fetcher import Fetcher
import logging

logging.basicConfig(level=logging.DEBUG)
config = get_scraper_config()
fetcher = Fetcher(config)

items = discover_otodom_investments(config, fetcher, identifier=None, limit=None)
print(f"Total global items found: {len(items)}")
