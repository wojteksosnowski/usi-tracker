import json
import os
from pathlib import Path

# Create a mapping from old_id to new_id by parsing the newly renamed files
data_dir = Path("Public/USIdata")

mapping = {}
for p in data_dir.rglob("master_IM-*.json"):
    data = json.load(open(p, encoding="utf-8"))
    # In my previous script, I didn't save the old ID, but wait, the master file itself might still contain members?
    pass

for p in data_dir.rglob("inv_master_IM-*.json"):
    pass

# Alternatively, I can just grep all usi_*.json for "MASTER-INV-" or "MST-"
for usi_file in data_dir.rglob("usi_*.json"):
    try:
        with open(usi_file, "r", encoding="utf-8") as f:
            u_data = json.load(f)
            
        old_id = u_data.get("master_id")
        if old_id and (old_id.startswith("MST-") or old_id.startswith("MASTER-")):
            print(f"Found orphaned reference to {old_id} in {usi_file}")
            # we need to find the correct new ID!
            # Since the new ID was generated and we don't have the map, we can search for a master file that has the SAME investments, or simply clear the master_id so it gets regenerated!
            # Let's see how many there are.
    except Exception as e:
        pass
