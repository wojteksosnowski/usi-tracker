import os
import json
import sys
from pathlib import Path

# Setup paths
sys.path.append(os.getcwd())
from python_worker import config
from python_worker.adapters import AdapterFactory, Merger

def fetch_and_transform_test():
    from usi_scrapers import api as scraper_api
    from usi_scrapers.models import ScraperConfig
    
    lib_config = config.get_scraper_config()
    
    # Let's pick a known investment
    portal = "rp"
    identifier = "16401" # Nowe Kolibki
    inv_slug = "nowe-kolibki-etap-4"
    dev_slug = "invest-komfort-spolka-akcyjna-spk"
    
    print(f"Fetching {portal} {identifier}...")
    res = scraper_api.fetch_investment(lib_config, None, portal, identifier)
    
    if res and "raw_details" in res:
        print("Transforming to unified schema...")
        unified = AdapterFactory.get_adapter(portal).transform(res["raw_details"], inv_slug, dev_slug)
        
        # Merge to get the final USI JSON
        final_usi = Merger.merge(rp_data=unified)
        
        print("\n--- FINAL USI JSON (from scraper) ---")
        print(json.dumps(final_usi, indent=2, ensure_ascii=False))
        
        with open("test_scraper_output.json", "w", encoding="utf-8") as f:
            json.dump(final_usi, f, indent=2, ensure_ascii=False)
    else:
        print("Fetch failed.")

if __name__ == "__main__":
    fetch_and_transform_test()
