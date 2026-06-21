import json
import os
from pathlib import Path
from python_worker.config import USI_DATA_DIR
import tempfile

def _atomic_write(path, data):
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

fixed = 0
for master_file in Path(USI_DATA_DIR).rglob("inv_master_*.json"):
    try:
        with open(master_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error {e}")
        continue
        
    if "primary_id" not in data and "members" in data and len(data["members"]) > 0:
        data["primary_id"] = data["members"][0].get("usi_inv_id")
        _atomic_write(master_file, data)
        fixed += 1
        print(f"Added primary_id {data['primary_id']} to {master_file.name}")

print(f"Fixed {fixed} master files.")
