import json
import os
from pathlib import Path
from python_worker.config import USI_DATA_DIR, DROPBOX_PATH
import tempfile

def _atomic_write(path, data):
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

master_dir = DROPBOX_PATH / "Public" / "USImaster"

# 1. Load all masters and their members
master_members = {}
for master_file in master_dir.glob("inv_master_*.json"):
    master_id = master_file.name.replace("inv_master_", "").replace(".json", "")
    try:
        with open(master_file, "r", encoding="utf-8") as f:
            mdata = json.load(f)
            members = mdata.get("members", [])
            member_ids = [m.get("usi_inv_id") for m in members if isinstance(m, dict)]
            master_members[master_id] = set(member_ids)
    except Exception as e:
        print(f"Error loading {master_file}: {e}")

print(f"Loaded {len(master_members)} masters.")

fixed = 0
for anchor in Path(USI_DATA_DIR).rglob("usi_*.json"):
    if "usi_dev_" in anchor.name: continue
    try:
        with open(anchor, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        continue
    
    master_id = data.get("master_id")
    usi_inv_id = data.get("usi_inv_id")
    
    if master_id:
        if master_id not in master_members:
            # handled by clean_dangling_masters.py
            pass
        else:
            if usi_inv_id not in master_members[master_id]:
                print(f"Orphaned member! {usi_inv_id} has master_id {master_id} but master doesn't list it. Clearing master_id.")
                data["master_id"] = None
                _atomic_write(anchor, data)
                fixed += 1

print(f"Fixed {fixed} orphaned members.")
