import json
import os
import time
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
                
                # Czas modyfikacji pliku lub data w srodku
                mtime = os.path.getmtime(path)
                
                # image_paths w unified json
                image_paths = data.get("image_paths", [])
                
                if not image_paths:
                    missing.append({
                        "file": str(path),
                        "id": data.get("usi_inv_id"),
                        "mtime": mtime,
                        "recent": mtime >= two_days_ago
                    })
            except Exception as e:
                pass

missing.sort(key=lambda x: x["mtime"], reverse=True)
print(f"Total missing images: {len(missing)}")
recent_count = sum(1 for m in missing if m["recent"])
print(f"Recent (last 3 days): {recent_count}")

print("Sample missing recent:")
for m in missing[:10]:
    print(f"- {m['id']} : {m['file']} (mtime: {time.ctime(m['mtime'])})")
