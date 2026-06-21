import json
import os
import time
import subprocess
from pathlib import Path

usi_data_dir = Path("Public/USIdata")
now = time.time()
two_days_ago = now - 3 * 24 * 3600

missing = []

for root, dirs, files in os.walk(usi_data_dir):
    for file in files:
        if file.startswith("usi_") and file.endswith(".json"):
            path = Path(root) / file
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                mtime = os.path.getmtime(path)
                image_paths = data.get("image_paths", [])
                
                if not image_paths and mtime >= two_days_ago:
                    dev_slug = path.parent.parent.name
                    inv_slug = path.parent.name
                    missing.append(f"{dev_slug}/{inv_slug}")
            except Exception as e:
                pass

print(f"Fixing {len(missing)} recent investments missing images...")
for slug in missing:
    print(f"Fixing {slug}...")
    subprocess.run(["./venv/bin/python", "-m", "python_worker.main", "update-inv", "--use-local-raw", slug], check=False)
