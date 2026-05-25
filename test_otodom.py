from usi_scrapers.fetcher import Fetcher
from usi_scrapers.models import ScraperConfig
from usi_scrapers.scraper_otodom import scrape_otodom
import json

config = ScraperConfig(public_dir="/tmp")
fetcher = Fetcher(config)

url = "https://www.otodom.pl/pl/inwestycja/aura-mokotow-ii-ID4ug2k"
result = scrape_otodom(url, fetcher)
print(json.dumps(result, indent=2))
