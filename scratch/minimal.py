import logging
logging.basicConfig(level=logging.INFO)

from python_worker.config import get_scraper_config
from usi_scrapers.fetcher import Fetcher
from usi_scrapers.api import process_batch

config = get_scraper_config()
fetcher = Fetcher(config)

targets = [{"identifier": "17702", "target_dir": None, "target_image_dir": None}]
print("Calling process_batch...")
process_batch(config, fetcher, "rp", targets)
print("Done.")
