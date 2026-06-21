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

from python_worker.investment_index import get_investment_index
idx = get_investment_index()

# 1. Collect all valid master_ids
valid_masters = set()
for master_file in Path(USI_DATA_DIR).rglob("inv_master_*.json"):
    master_id = master_file.name.replace("inv_master_", "").replace(".json", "")
    valid_masters.add(master_id)

print(f"Found {len(valid_masters)} valid master files.")

# 2. Check all anchors
fixed = 0
for anchor in Path(USI_DATA_DIR).rglob("usi_*.json"):
    if "usi_dev_" in anchor.name: continue
    try:
        with open(anchor, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        continue
    
    master_id = data.get("master_id")
    if master_id and master_id not in valid_masters:
        print(f"Clearing dangling master_id {master_id} from {anchor.parent.name}")
        data["master_id"] = None
        _atomic_write(anchor, data)
        fixed += 1

print(f"Fixed {fixed} dangling master_ids.")
