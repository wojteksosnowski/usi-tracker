import json
import os
from pathlib import Path

data_dir = Path("Public/USIdata")
member_to_master = {}

for p in data_dir.rglob("master_IM-*.json"):
    data = json.load(open(p, encoding="utf-8"))
    m_id = data.get("master_id")
    for inv_id in data.get("investments", []):
        member_to_master[inv_id] = m_id

for p in data_dir.rglob("inv_master_IM-*.json"):
    data = json.load(open(p, encoding="utf-8"))
    m_id = data.get("master_id")
    for inv_id in data.get("investments", []):
        member_to_master[inv_id] = m_id

# Now update all usi_*.json files
for usi_file in data_dir.rglob("usi_*.json"):
    with open(usi_file, "r", encoding="utf-8") as f:
        u_data = json.load(f)
        
    old_id = u_data.get("master_id")
    inv_id = u_data.get("usi_inv_id")
    
    # If the file has an old orphaned master ID, or if it is in member_to_master and not updated
    if inv_id in member_to_master:
        correct_master_id = member_to_master[inv_id]
        if old_id != correct_master_id:
            print(f"Fixing {usi_file}: changing master_id from {old_id} to {correct_master_id}")
            u_data["master_id"] = correct_master_id
            
            import tempfile
            fd, temp_path = tempfile.mkstemp(dir=usi_file.parent, text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as tf:
                json.dump(u_data, tf, indent=2, ensure_ascii=False)
            os.replace(temp_path, usi_file)

