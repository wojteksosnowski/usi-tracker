import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")
from python_worker.config import get_scraper_config
from python_worker.services.scraper_gateway import ScraperGateway

config = get_scraper_config()
gateway = ScraperGateway(config)
items = gateway.list_investments("oto", "10556292")
print(f"Found {len(items)} items for Profbud.")
