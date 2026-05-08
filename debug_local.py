import logging
import sys
from pathlib import Path
import os
import json

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append("/Volumes/Samsam/claude-py/usi-scrapers")

from python_worker.config import USI_DATA_DIR
from usi_scrapers.adapters.otodom import OtodomAdapter

logging.basicConfig(level=logging.INFO)

dev_slug = "acatom"
inv_slug = "daszynskiego-park"
inv_dir = USI_DATA_DIR / dev_slug / inv_slug

# Try to find a raw file
raw_files = list(inv_dir.glob("raw_oto_*.json"))
if not raw_files:
    print(f"No raw Otodom files found in {inv_dir}")
    sys.exit(1)

raw_path = raw_files[0]
print(f"Testing transformation with: {raw_path.name}")

with open(raw_path, "r") as f:
    raw_data = json.load(f)

try:
    unified = OtodomAdapter.transform(raw_data, inv_slug, dev_slug)
    print("Success!")
    print(f"Name: {unified.get('name')}")
    print(f"Images: {unified.get('images_count')}")
    print(f"Price: {unified.get('financials', {}).get('price_min')}")
except Exception as e:
    import traceback
    traceback.print_exc()
