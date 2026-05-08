import logging
import json
import re
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
ad = data.get("ad")
if ad:
    bread = ad.get("breadcrumbs", [])
    if bread:
        last = bread[-1]
        print(f"Last breadcrumb: {last}")
