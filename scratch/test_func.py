from usi_scrapers.api import get_scraper_func
func = get_scraper_func("rp", "scrape")
print(func.__name__)
import inspect
print(inspect.signature(func))
