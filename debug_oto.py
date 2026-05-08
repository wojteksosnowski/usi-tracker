import logging
import sys
from pathlib import Path
import os

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")

from python_worker.config import get_scraper_config
from usi_scrapers.fetcher import Fetcher
from usi_scrapers.scraper_otodom import scrape_otodom

logging.basicConfig(level=logging.INFO)

config = get_scraper_config()
fetcher = Fetcher(config)

url = "https://www.otodom.pl/pl/oferta/daszynskiego-park-ID4A4Gb"
dev_slug = "acatom"
inv_slug = "daszynskiego-park"

print(f"Testing Otodom scrape for: {url}")
try:
    result = scrape_otodom(url, dev_slug, inv_slug, fetcher)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Success!")
        print(f"Name: {result.get('title')}")
        print(f"Images: {len(result.get('image_urls', []))}")
except Exception as e:
    import traceback
    traceback.print_exc()
