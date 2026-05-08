import logging
import json
from usi_scrapers.scraper_to import fetch_to_html, parse_to_product, _investment_image_prefix
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config

logging.basicConfig(level=logging.INFO)
config = get_scraper_config()
fetcher = Fetcher(config)

url = "https://tabelaofert.pl/inwestycja/la-vie-house-lagiewnicka-krakow-podgorze-mieszkania-na-sprzedaz,i8935962"
html = fetch_to_html(url, fetcher)
product = parse_to_product(html)

images = product.get("image", [])
if isinstance(images, str): images = [images]

print(f"JSON-LD Images ({len(images)}):")
for i, img in enumerate(images):
    print(f"  [{i}] {img}")
    print(f"      Prefix: {_investment_image_prefix(str(img))}")
