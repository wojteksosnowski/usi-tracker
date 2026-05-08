import logging
import json
from pathlib import Path
from usi_scrapers.scraper_otodom import fetch_otodom_html, extract_next_data
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config

logging.basicConfig(level=logging.INFO)
config = get_scraper_config()
fetcher = Fetcher(config)

url = "https://www.otodom.pl/pl/inwestycja/poczatek-polnocy-ID4mYvY"
html = fetch_otodom_html(url, fetcher)
data = extract_next_data(html)
print(f"Data keys: {list(data.keys())}")
if "ad" in data:
    print("Found 'ad' key")
    print(f"Ad keys: {list(data['ad'].keys())}")
elif "data" in data:
    print("Found 'data' key")
    print(f"Data sub-keys: {list(data['data'].keys())}")
    if "investment" in data["data"]:
        print("Found 'investment' key")
        print(f"Investment keys: {list(data['data']['investment'].keys())}")
else:
    print("Neither 'ad' nor 'data' found at top level of pageProps")
    # print(json.dumps(data, indent=2)[:1000])
