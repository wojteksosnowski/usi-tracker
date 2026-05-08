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

# YIT Investment
url = "https://www.otodom.pl/pl/inwestycja/poczatek-polnocy-ID4mYvY"
html = fetch_otodom_html(url, fetcher)
data = extract_next_data(html)
ad = data.get("ad")
if ad:
    print(f"URL: {url}")
    print(f"Agency: {ad.get('agency')}")
    print(f"AdvertiserType: {ad.get('advertiserType')}")

# Victoria Dom Investment
url2 = "https://www.otodom.pl/pl/inwestycja/metro-art-ID4lTye"
html2 = fetch_otodom_html(url2, fetcher)
data2 = extract_next_data(html2)
ad2 = data2.get("ad")
if ad2:
    print(f"\nURL: {url2}")
    print(f"Agency: {ad2.get('agency')}")
    print(f"AdvertiserType: {ad2.get('advertiserType')}")
