import json
from pathlib import Path

data_dir = Path("Public/USIdata")
count = 0
for p in data_dir.rglob("usi_*.json"):
    if "usi_dev_" in p.name: continue
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "usi_inv_id" not in data and data.get("status") == "Brak" and data.get("reviewed") is False:
            print(f"Deleting broken skeleton: {p}")
            p.unlink()
            count += 1
    except Exception as e:
        print(f"Error reading {p}: {e}")

print(f"Deleted {count} broken skeletons.")
