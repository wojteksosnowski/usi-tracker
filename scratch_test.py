import json
from pathlib import Path
from usi_scrapers.api import transform_to_unified

# Load a raw Otodom file
raw_files = list(Path("Public/USIdata").rglob("raw_oto_*.json"))
if raw_files:
    data = json.loads(raw_files[0].read_text())
    meta = transform_to_unified("otodom", data, entity_type="investment")
    print(meta)
