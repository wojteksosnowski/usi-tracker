import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.adapters import AdapterFactory
from python_worker.adapters.utils import JsonPathExtractor

# MOCK DATA SAMPLES
MOCK_RP = {
    "id": 123,
    "slug": "rp-inv",
    "vendor": {"type": "obj", "value": {"id": 456, "name": "RP Dev", "slug": "rp-dev-slug"}},
    "stats": {"type": "obj", "value": {
        "ranges_price_min": 400000,
        "ranges_height_max": 275
    }}
}

MOCK_OTO = {
    "id": 999,
    "slug": "oto-inv",
    "agency": {"id": 888, "name": "OTO Dev", "slug": "oto-dev-slug"},
    "topInformation": [
        {"label": "number_of_units_in_project", "values": ["50"]}
    ],
    "target": {"Price": 600000}
}

MOCK_TO = {
    "id": "8975118",
    "slug": "to-inv",
    "brand": {"id": "1234", "name": "TO Dev", "slug": "to-dev-slug"},
    "offers": [{"lowPrice": 300000, "highPrice": 500000}],
    "additionalProperty": [
        {"name": "Wysokość pomieszczeń", "value": "270 cm"}
    ]
}

def run_comparison():
    print("--- ADAPTER COMPARISON TEST ---")
    
    with open("python_worker/schemas/portal_data_mapping.json", "r") as f:
        mapping = json.load(f)["portals"]

    print("\n[TO] Testing Transformation (Atal Aura logic):")
    to_unified = AdapterFactory.get_adapter("to").transform(MOCK_TO, "to-inv", "to-dev")
    # TabelaOfert adapter URL generation:
    # url = f"https://tabelaofert.pl/nowe-nieruchomosci/{vendor_slug}/{offer_slug}" 
    # (Note: actual TO URL building might vary, but we check if it picked up the slug)
    print(f"Developer Name:  {to_unified['developer']}")
    print(f"Developer ID:    {to_unified['sources']['to'].get('brand_id') or to_unified['sources']['to'].get('developer_id')}")
    print(f"Investment URL:  {to_unified['sources']['to'].get('url')}")

    print("\n[OTO] Testing Transformation:")
    oto_unified = AdapterFactory.get_adapter("oto").transform(MOCK_OTO, "oto-inv", "oto-dev")
    print(f"Developer ID:    {oto_unified['sources']['oto'].get('agency_id')}")
    print(f"Investment URL:  {oto_unified['sources']['oto'].get('url')}")

    print("\n[RP] Testing Transformation (Unwrapping):")
    rp_unified = AdapterFactory.get_adapter("rp").transform(MOCK_RP, "rp-inv", "rp-dev")
    print(f"Vendor ID:       {rp_unified['sources']['rp'].get('vendor_id')}")
    # URL: https://rynekpierwotny.pl/oferty/{vendor_slug}/{offer_slug}-{offer_id}/
    print(f"Investment URL:  {rp_unified['sources']['rp'].get('url')}")
    if "rp-dev-slug" in (rp_unified['sources']['rp'].get('url') or ""):
        print("SUCCESS: RP URL contains correct vendor slug.")
    else:
        print("FAILURE: RP URL has wrong slug.")

if __name__ == "__main__":
    run_comparison()
