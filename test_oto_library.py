import logging
from pathlib import Path
from usi_scrapers import api as scraper_api
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config

logging.basicConfig(level=logging.INFO)
config = get_scraper_config()
fetcher = Fetcher(config)

url = "https://www.otodom.pl/pl/inwestycja/poczatek-polnocy-ID4mYvY"
print(f"Testing URL: {url}")
res = scraper_api.fetch_investment(config, fetcher, "oto", url, "yit-development", "poczatek-polnocy")
if "error" in res:
    print(f"Error: {res['error']}")
else:
    print(f"Success! Title: {res.get('title')}")
    print(f"Agency: {res.get('agency_name')}")
