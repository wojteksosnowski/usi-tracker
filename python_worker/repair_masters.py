import json
import os
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from python_worker.investment_index import get_investment_index
import tempfile

def _atomic_write(path, data):
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

idx = get_investment_index()

for master_file in Path(USI_DATA_DIR).rglob("inv_master_*.json"):
    data = _read_json(master_file)
    if not data or "members" not in data: continue
    
    master_id = data.get("master_id")
    valid_members = []
    
    for m in data["members"]:
        inv_id = m.get("usi_inv_id")
        entry = idx.get_by_id(inv_id)
        if not entry:
            print(f"Skipping missing member {inv_id}")
            continue
        
        anchor_path = None
        # find anchor path
        folder = Path(entry["folder_path"])
        if not folder.is_absolute():
            folder = Path(USI_DATA_DIR).parent.parent / folder
            
        for f in folder.glob("usi_*.json"):
            if "usi_dev_" not in f.name:
                anchor_path = f
                break
                
        if anchor_path:
            anchor_data = _read_json(anchor_path)
            if anchor_data and anchor_data.get("master_id") == master_id:
                valid_members.append(m)
            else:
                print(f"Member {inv_id} does not have master_id={master_id}. Removing from master.")
        else:
            print(f"No anchor found for {inv_id} in {folder}")
            
    if len(valid_members) != len(data["members"]):
        if len(valid_members) <= 1:
            print(f"Group {master_id} has <= 1 members. Dissolving.")
            if len(valid_members) == 1:
                last_id = valid_members[0]["usi_inv_id"]
                last_entry = idx.get_by_id(last_id)
                folder = Path(last_entry["folder_path"])
                if not folder.is_absolute(): folder = Path(USI_DATA_DIR).parent.parent / folder
                for f in folder.glob("usi_*.json"):
                    if "usi_dev_" not in f.name:
                        a_data = _read_json(f)
                        if a_data and a_data.get("master_id") == master_id:
                            a_data["master_id"] = None
                            _atomic_write(f, a_data)
                            print(f"Cleared master_id from last member {last_id}")
                        break
            master_file.unlink()
        else:
            print(f"Updating group {master_id} with {len(valid_members)} members.")
            data["members"] = valid_members
            _atomic_write(master_file, data)

