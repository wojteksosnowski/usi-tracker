import sys
from usi_scrapers import fetcher
from usi_scrapers import scraper_to
from usi_scrapers.models import ScraperConfig

config = ScraperConfig(public_dir="/Volumes/Samsam/claude-py/usi-tracker/Public")
f = fetcher.Fetcher(config)
html = scraper_to.fetch_to_html("https://tabelaofert.pl/inwestycja/astelia-park-etap-iii-leona-berensona-warszawa-bialoleka-grodzisk-mieszkania-na-sprzedaz,i9227311", f)
with open("test_to.html", "w") as out:
    if html:
        out.write(html)
