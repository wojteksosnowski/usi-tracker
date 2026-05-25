import json
from pathlib import Path
import os

dev_dir = Path("/Volumes/Samsam/Public/USIdev")
count = 0

for json_file in dev_dir.rglob("usi_dev_*.json"):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        changed = False
        
        if "master_id" in data:
            del data["master_id"]
            changed = True
            
        if "is_master" in data:
            del data["is_master"]
            changed = True
            
        if "merged_from" in data:
            del data["merged_from"]
            changed = True
            
        if "suggestions" in data:
            del data["suggestions"]
            changed = True
            
        if changed:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            count += 1
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

print(f"Cleaned up {count} files.")
