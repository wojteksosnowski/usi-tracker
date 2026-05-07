import json
import logging
from python_worker.scraper_otodom import fetch_otodom_html, extract_next_data

logging.basicConfig(level=logging.INFO)

def audit_otodom_item():
    url = "https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/cala-polska?limit=72&investmentEstateType=FLATS&by=LATEST&direction=DESC&viewType=listing"
    html = fetch_otodom_html(url)
    data = extract_next_data(html)
    
    # Common path for listings
    search_ads = data.get("data", {}).get("searchAds", {})
    if not search_ads:
        search_ads = data.get("props", {}).get("pageProps", {}).get("data", {}).get("searchAds", {})
        
    items = search_ads.get("items", [])
    if items:
        print("KEYS IN FIRST ITEM:", items[0].keys())
        print("SAMPLE ITEM:", json.dumps(items[0], indent=2)[:500])
    else:
        print("No items found.")

if __name__ == "__main__":
    audit_otodom_item()
