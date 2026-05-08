import logging
import json
from usi_scrapers.scraper_to import scrape_tabelaofert
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config

logging.basicConfig(level=logging.INFO)
config = get_scraper_config()
fetcher = Fetcher(config)

url = "https://tabelaofert.pl/inwestycja/la-vie-house-lagiewnicka-krakow-podgorze-mieszkania-na-sprzedaz,i8935962"
res = scrape_tabelaofert(url, "imperial-capital", "la-vie-house-lagiewnicka-krakow-podgorze-mieszkania-na-sprzedaz", fetcher)

print(f"Scrape returned {len(res.get('image_urls', []))} images")
for u in res.get('image_urls', [])[:20]:
    print(f"  {u}")

if len(res.get('image_urls', [])) > 50:
    print("WARNING: Too many images returned!")
