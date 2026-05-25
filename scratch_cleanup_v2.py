from pathlib import Path
import json
import re
from python_worker.config import USI_DATA_DIR

data_dir = Path(USI_DATA_DIR)

stats = {"renamed_usi": 0, "extracted_ids": 0}

for dev_dir in data_dir.iterdir():
    if not dev_dir.is_dir() or dev_dir.name.startswith("."): continue
    
    for inv_dir in dev_dir.iterdir():
        if not inv_dir.is_dir(): continue
        
        usi_files = list(inv_dir.glob("usi_*.json"))
        
        for usi_file in usi_files:
            parts = usi_file.stem.split("_")
            if len(parts) == 3 and parts[1] in ("rp", "oto", "to"):
                continue # Already canonical
                
            try:
                data = json.loads(usi_file.read_text(encoding="utf-8"))
            except:
                continue
            
            changed = False
            sources = data.get("sources", {})
            active_portal = None
            active_id = None
            
            for portal, p_data in sources.items():
                if not p_data: continue
                if p_data.get("id"):
                    active_portal = portal
                    active_id = p_data.get("id")
                    break
                elif p_data.get("url"):
                    # Extract ID from URL
                    url = p_data["url"]
                    if portal == "oto" and "-ID" in url:
                        extracted = url.split("-ID")[-1]
                        p_data["id"] = extracted
                        active_portal = portal
                        active_id = extracted
                        changed = True
                        stats["extracted_ids"] += 1
                        break
                    elif portal == "rp":
                        # Usually rp id is in agency_id or url but let's check vendor_id
                        pass
            
            if active_portal and active_id:
                canonical_name = f"usi_{active_portal}_{active_id}.json"
                if usi_file.name != canonical_name:
                    new_path = inv_dir / canonical_name
                    if changed:
                        new_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                        usi_file.unlink()
                    else:
                        usi_file.rename(new_path)
                    
                    stats["renamed_usi"] += 1
                    changed = False 
            
            if changed:
                usi_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                
print(f"Cleanup v2 finished: {stats}")
