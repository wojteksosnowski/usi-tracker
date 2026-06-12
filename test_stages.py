import json
from usi_scrapers.scraper_rp import _parse_rp_results
import sys

# Read one page of offer-list
import subprocess
out = subprocess.check_output(['curl', '-s', 'https://rynekpierwotny.pl/api/v2/offers/offer/?s=offer-list&page=1&page_size=30'])
data = json.loads(out)
results = data.get("results", [])

offers = _parse_rp_results(results)
print(f"Results: {len(results)}, Offers: {len(offers)}")
