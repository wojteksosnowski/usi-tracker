from usi_scrapers.scraper_rp import scrape_rynek_pierwotny
from usi_scrapers.fetcher import Fetcher
from usi_scrapers.models import ScraperConfig

config = ScraperConfig(public_dir="/tmp")
fetcher = Fetcher(config)

result = scrape_rynek_pierwotny("20360", fetcher)
print(result)
