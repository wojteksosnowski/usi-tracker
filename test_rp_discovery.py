import logging
import json
from usi_scrapers import api as scraper_api
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config
from python_worker.portal_matcher import filter_new_investments

logging.basicConfig(level=logging.INFO)
config = get_scraper_config()
fetcher = Fetcher(config)

print(f"RP Discovery URLs: {config.rp_discovery_urls}")

print("\n--- Raw Library Call ---")
raw_results = scraper_api.list_investments(config, fetcher, "rp")
print(f"Found {len(raw_results)} raw items")
if raw_results:
    print("First item preview:")
    print(json.dumps(raw_results[0], indent=2))

print("\n--- Filtered Call ---")
filtered = filter_new_investments(raw_results, "rp")
print(f"Found {len(filtered)} filtered items")
new_items = [i for i in filtered if i.get("is_new")]
print(f"New items: {len(new_items)}")
