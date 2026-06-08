import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

# Setup path
_BASE_DIR = Path.cwd()
sys.path.insert(0, str(_BASE_DIR))
lib_path = str(_BASE_DIR.parent / "usi-scrapers")
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

from python_worker.config import get_shared_fetcher

def main():
    fetcher = get_shared_fetcher()
    if not fetcher:
        print("Error: Could not get shared fetcher.")
        return

    # Use the actual discovery URL
    url = "https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/cala-polska?limit=72&investmentEstateType=FLATS&by=LATEST&direction=DESC&viewType=listing"
    print(f"\n--- Testing fetcher for {url} ---")
    
    try:
        html = fetcher.fetch(url)
        
        if html:
            print(f"Success! Fetched {len(html)} chars.")
            low_html = html.lower()
            if "otodom" in low_html and "__next_data__" in low_html:
                print("HTML content seems valid (found 'otodom' and '__NEXT_DATA__').")
            elif "px-captcha" in low_html or "perimeterx" in low_html:
                print("WARNING: Bot protection triggered (PerimeterX/Captcha)!")
            else:
                print("HTML content does NOT contain expected keywords.")
                print(f"Preview (first 500 chars): {html[:500]}")
        else:
            print("Fetched HTML is empty or None.")

    except Exception as e:
         print(f"Exception during fetch: {e}")

if __name__ == "__main__":
    main()
