import sys
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")
from python_worker.config import get_scraper_config
from usi_scrapers.scraper_otodom import fetch_otodom_html, extract_next_data, normalize_to_legacy_props
from usi_scrapers.fetcher import Fetcher
import json

config = get_scraper_config()
fetcher = Fetcher(config)
html = fetch_otodom_html("https://www.otodom.pl/pl/firmy/deweloperzy/deweloper-ID10556292?limit=72&currentPage=1", fetcher)
full_data = extract_next_data(html)
data = normalize_to_legacy_props(full_data, "oto")

search_ads = data.get("data", {}).get("searchAds", {})
if not search_ads:
    search_ads = data.get("searchAds", {})

items = search_ads.get("items", [])
print(f"Total items in JSON: {len(items)}")
for i, it in enumerate(items[:10]):
    print(f"Item {i}: id={it.get('id')}, slug={it.get('slug')}")
