import logging
import json
from usi_scrapers.scraper_to import fetch_to_html, extract_to_data, filter_investment_images
from usi_scrapers.fetcher import Fetcher
from python_worker.config import get_scraper_config

logging.basicConfig(level=logging.INFO)
config = get_scraper_config()
fetcher = Fetcher(config)

url = "https://tabelaofert.pl/inwestycja/la-vie-house-lagiewnicka-krakow-podgorze-mieszkania-na-sprzedaz,i8935962"
print(f"Debugging URL: {url}")

html = fetch_to_html(url, fetcher)
if not html:
    print("Could not fetch HTML")
    exit(1)

product = extract_to_data(html, url)
main_image = product.get("image")
gallery_urls = product.get("_raw_gallery_urls", [])

print(f"Main Image: {main_image}")
print(f"Total Raw Gallery URLs: {len(gallery_urls)}")

filtered = filter_investment_images(gallery_urls, product)
print(f"Filtered Gallery URLs: {len(filtered)}")

for u in filtered[:10]:
    print(f"  {u}")

from usi_scrapers.scraper_to import _investment_image_prefix
prefix = _investment_image_prefix(str(main_image[0] if isinstance(main_image, list) else main_image))
print(f"Calculated Prefix: {prefix}")
