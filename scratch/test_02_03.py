import logging
from pathlib import Path
from usi_scrapers.models import ScraperConfig
from usi_scrapers.fetcher import Fetcher
import usi_scrapers.api as api

logging.basicConfig(level=logging.INFO)

config = ScraperConfig(public_dir=Path("/tmp/usi_test_public"))
fetcher = Fetcher(config)

target_dir = Path("/tmp/usi_test_public/USIdata/test-dev/test-inv")
target_image_dir = Path("/tmp/usi_test_public/USI/test-dev/test-inv")

targets = [{
    "identifier": "17702",
    "target_dir": target_dir,
    "target_image_dir": target_image_dir
}]

try:
    results = api.process_batch(config, fetcher, "rp", targets)
    print("Results:", results)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()

