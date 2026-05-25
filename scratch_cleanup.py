from pathlib import Path
import json
import uuid
import shutil
from python_worker.config import USI_DATA_DIR

data_dir = Path(USI_DATA_DIR)

def generate_usi_id(prefix="INV"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

stats = {"renamed_usi": 0, "backfilled_ids": 0, "archived_raws": 0}

for dev_dir in data_dir.iterdir():
    if not dev_dir.is_dir() or dev_dir.name.startswith("."): continue
    
    for inv_dir in dev_dir.iterdir():
        if not inv_dir.is_dir(): continue
        
        # 1. Resolve non-canonical naming & 2. Fix schema
        usi_files = list(inv_dir.glob("usi_*.json"))
        
        for usi_file in usi_files:
            try:
                data = json.loads(usi_file.read_text(encoding="utf-8"))
            except:
                continue
            
            changed = False
            
            # Check schema (usi_inv_id)
            if not data.get("usi_inv_id"):
                data["usi_inv_id"] = generate_usi_id("INV")
                changed = True
                stats["backfilled_ids"] += 1
                
            # Check canonical naming
            # Canonical name is usi_{portal}_{portal_id}.json
            # Find the active portal (the one with 'id' in sources)
            sources = data.get("sources", {})
            active_portal = None
            active_id = None
            for portal, p_data in sources.items():
                if p_data and p_data.get("id"):
                    active_portal = portal
                    active_id = p_data.get("id")
                    break
            
            if active_portal and active_id:
                canonical_name = f"usi_{active_portal}_{active_id}.json"
                if usi_file.name != canonical_name:
                    # Need to rename
                    new_path = inv_dir / canonical_name
                    if changed:
                        # Write to new path directly
                        new_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                        usi_file.unlink()
                    else:
                        usi_file.rename(new_path)
                    
                    stats["renamed_usi"] += 1
                    changed = False # already handled
            
            if changed:
                # Just save it back
                usi_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                
        # 3. Cleanup duplicate raw files
        # A folder should ideally have one raw_{portal}_{portal_id}.json for the active portal.
        # Let's archive legacy raw files (those with timestamps) IF a canonical raw file exists for that portal.
        for portal in ["rp", "oto", "to"]:
            raw_files = list(inv_dir.glob(f"raw_{portal}_*.json"))
            if len(raw_files) <= 1:
                continue
                
            # Check if canonical exists
            canonical_raw = None
            for rf in raw_files:
                parts = rf.stem.split("_")
                if len(parts) == 3 and parts[1] == portal:
                    # it's raw_{portal}_{id}.json
                    canonical_raw = rf
                    break
                    
            if canonical_raw:
                # Archive all others
                archive_dir = inv_dir / "_archive"
                for rf in raw_files:
                    if rf != canonical_raw:
                        archive_dir.mkdir(exist_ok=True)
                        rf.rename(archive_dir / rf.name)
                        stats["archived_raws"] += 1

print(f"Cleanup finished: {stats}")
