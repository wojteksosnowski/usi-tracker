import os
import shutil
from pathlib import Path

data_dir = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata")
for inv_dir in data_dir.rglob("*"):
    if not inv_dir.is_dir(): continue
    ratings = inv_dir / "ratings.json"
    if ratings.exists():
        # Znajdź plik usi_...
        anchor = None
        for f in inv_dir.glob("usi_*.json"):
            if not f.name.startswith("usi_stage_stub"):
                anchor = f
                break
        
        if anchor:
            meta_name = anchor.name.replace("usi_", "meta_")
            meta_file = inv_dir / meta_name
            shutil.move(ratings, meta_file)
            print(f"Migrated {ratings} -> {meta_file}")
        else:
            print(f"Cannot migrate {ratings} - no anchor found")

print("Done")
