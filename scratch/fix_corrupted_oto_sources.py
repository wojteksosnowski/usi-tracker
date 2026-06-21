import os
import json
from pathlib import Path

def fix_corrupted_oto_sources():
    data_dir = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata")
    fixed_count = 0
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith("usi_") and file.endswith(".json"):
                filepath = Path(root) / file
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    changed = False
                    sources = data.get("sources", {})
                    oto_source = sources.get("oto", {})
                    
                    if "agency_id" in oto_source and "id" not in oto_source:
                        oto_source["id"] = oto_source.pop("agency_id")
                        if "agency_ids" in oto_source:
                            del oto_source["agency_ids"]
                        changed = True
                    
                    if changed:
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        fixed_count += 1
                        print(f"Fixed: {filepath.relative_to(data_dir)}")
                        
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    
    print(f"Total files fixed: {fixed_count}")

if __name__ == "__main__":
    fix_corrupted_oto_sources()
