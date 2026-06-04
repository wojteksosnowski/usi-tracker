import sys
from pathlib import Path

# Ensure usi-scrapers can be imported
sys.path.insert(0, str(Path("venv/lib/python3.13/site-packages").absolute()))

from usi_scrapers.mapping import transform_to_unified

def main():
    print("Testing Otodom transformation")
    oto_raw = {
        "ad": {
            "title": "Test Otodom",
            "target": {
                "Price": "550000.50"
            },
            "topInformation": [
                {
                    "label": "project_finish_date",
                    "values": ["2026-05-15"]
                }
            ],
            "characteristics": [
                {
                    "key": "price_per_m",
                    "value": "15000"
                }
            ]
        }
    }
    
    oto_mapped = transform_to_unified("oto", oto_raw)
    print(f"Oto mapped price_min: {oto_mapped.get('price_min')} (type: {type(oto_mapped.get('price_min'))})")
    print(f"Oto mapped price_m2_min: {oto_mapped.get('price_m2_min')} (type: {type(oto_mapped.get('price_m2_min'))})")
    print(f"Oto mapped delivery_date: {oto_mapped.get('delivery_date')}")
    
    assert isinstance(oto_mapped.get('price_min'), float)
    assert oto_mapped.get('delivery_date') == "2026-Q2"
    
    print("\nTesting RynekPierwotny transformation")
    rp_raw = {
        "name": "Test RP",
        "stats": {
            "ranges_price_min": "450000,50",
            "ranges_price_max": "1000000"
        }
    }
    rp_mapped = transform_to_unified("rp", rp_raw)
    print(f"RP mapped price_min: {rp_mapped.get('price_min')} (type: {type(rp_mapped.get('price_min'))})")
    print(f"RP mapped price_max: {rp_mapped.get('price_max')} (type: {type(rp_mapped.get('price_max'))})")
    
    assert isinstance(rp_mapped.get('price_min'), float)
    assert rp_mapped.get('price_min') == 450000.5
    assert rp_mapped.get('price_max') == 1000000.0
    
    print("\nAll transformations passed successfully!")

if __name__ == "__main__":
    main()
