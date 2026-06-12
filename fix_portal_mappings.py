import json
from pathlib import Path

usi_data_dir = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata")
fixed_count = 0

for file_path in usi_data_dir.rglob("usi_*.json"):
    if "usi_dev_" in file_path.name: continue
    
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            continue
            
    sources = data.get("sources", {})
    changed = False
    new_sources = {}
    
    for portal, source_data in sources.items():
        url = source_data.get("url", "")
        real_portal = portal
        
        if "otodom.pl" in url and portal != "oto":
            real_portal = "oto"
            changed = True
        elif "rynekpierwotny.pl" in url and portal != "rp":
            real_portal = "rp"
            changed = True
        elif "tabelaofert.pl" in url and portal != "to":
            real_portal = "to"
            changed = True
            
        new_sources[real_portal] = source_data
        
    if changed:
        data["sources"] = new_sources
        # Fix usi_inv_id if it's the anchor
        current_id = data.get("usi_inv_id", "")
        new_id = current_id
        
        if current_id.startswith("to_") and "otodom.pl" in str(data["sources"]):
            # Find the actual portal by checking the id value
            for p, d in new_sources.items():
                if d.get("id") == current_id[3:]:
                    new_id = f"{p}_{current_id[3:]}"
                    break
                    
        # Update IDs
        if new_id != current_id:
            data["usi_inv_id"] = new_id
            
        # Write back
        new_path = file_path.parent / f"usi_{new_id}.json" if new_id != current_id else file_path
        
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        if new_path != file_path:
            file_path.unlink()
            
        fixed_count += 1
        print(f"Fixed {file_path.name} -> {new_path.name} (sources updated)")

print(f"Fixed {fixed_count} files.")
