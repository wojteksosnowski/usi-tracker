from usi_scrapers.mapping import transform_to_unified
import json
with open('Public/USIdata/sgi/drucianka-wschodnia/raw_oto_4ByK6.json', 'r') as f:
    raw = json.load(f)
unified = transform_to_unified("oto", raw, "investment")
print("keys:", unified.keys())
print("image_urls length:", len(unified.get("image_urls", [])))
