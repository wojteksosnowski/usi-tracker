import json
import os
from usi_scrapers.fetcher import Fetcher
from usi_scrapers.models import ScraperConfig
from usi_scrapers.scraper_rp import scrape_rynek_pierwotny

config = ScraperConfig(public_dir="/tmp", scraperapi_key=os.environ.get("SCRAPERAPI_KEY", ""))
fetcher = Fetcher(config)

result = scrape_rynek_pierwotny("17906", fetcher)
images = result.get('image_urls', [])
print(f"Liczba zdjęć w image_urls: {len(images)}")
if images:
    print(f"Przykładowe zdjęcie: {images[0]}")
