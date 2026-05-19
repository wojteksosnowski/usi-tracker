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
    "vendor": {"type": "obj", "value": {"id": 456, "name": "RP Dev"}},
    "stats": {"type": "obj", "value": {
        "ranges_price_min": 400000,
        "ranges_height_max": 275
    }}
}

MOCK_OTO = {
    "ad": {
        "id": 999,
        "slug": "oto-inv",
        "agency": {"id": 888, "name": "OTO Dev"},
        "topInformation": [
            {"label": "number_of_units_in_project", "values": ["50"]}
        ],
        "target": {"Price": 600000}
    }
}

MOCK_TO = {
    "id": "8975118",
    "slug": "to-inv",
    "brand": {"id": "1234", "name": "TO Dev"},
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
    to_unified = AdapterFactory.get_adapter("to").transform(MOCK_TO, "atal-aura", "atal-s-a")
    print(f"Investment Name: {to_unified['name']}")
    print(f"Developer Name:  {to_unified['developer']}")
    print(f"Investment ID:   {to_unified['sources']['to'].get('id')}")
    print(f"Developer ID:    {to_unified['sources']['to'].get('developer_id')}")
    print(f"Ceiling Height:  {to_unified['specifications'].get('ceiling_height_max')}m")
    print(f"Price Range:     {to_unified['financials'].get('price_min')} - {to_unified['financials'].get('price_max')}")

    print("\n[OTO] Testing Transformation:")
    oto_unified = AdapterFactory.get_adapter("oto").transform(MOCK_OTO, "oto-inv", "oto-dev")
    print(f"Investment ID:   {oto_unified['sources']['oto'].get('id')}")
    print(f"Developer ID:    {oto_unified['sources']['oto'].get('agency_id')}")
    print(f"Units Count:     {oto_unified['specifications'].get('units_count')}")
    print(f"Price Min:       {oto_unified['financials'].get('price_min')}")

    print("\n[RP] Testing Transformation (Unwrapping):")
    rp_unified = AdapterFactory.get_adapter("rp").transform(MOCK_RP, "rp-inv", "rp-dev")
    print(f"Investment ID:   {rp_unified['sources']['rp'].get('id')}")
    print(f"Vendor ID:       {rp_unified['sources']['rp'].get('vendor_id')}")
    print(f"Price Min:       {rp_unified['financials'].get('price_min')}")
    print(f"Ceiling Max:     {rp_unified['specifications'].get('ceiling_height_max')}m")

if __name__ == "__main__":
    run_comparison()
