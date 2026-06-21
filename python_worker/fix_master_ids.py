import json
from pathlib import Path
import os
import sys

# Setup paths so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.developer_indexer import DeveloperIndexer
import python_worker.investment_index as inv_index

def fix_master_ids():
    data_dir = Path("Public/USIdata")
    indexer = DeveloperIndexer(None)
    
    # Znajdź wszystkie pliki master_*.json lub inv_master_*.json, które mają stare ID
    master_files = []
    master_files.extend(data_dir.rglob("master_MST-*.json"))
    master_files.extend(data_dir.rglob("inv_master_MASTER-*.json"))
    master_files.extend(data_dir.rglob("master_MASTER-*.json"))
    
    # We want to process each unique old_master_id only once per directory
    processed_dirs = set()
    
    for master_file in master_files:
        inv_dir = master_file.parent
        
        try:
            with open(master_file, "r", encoding="utf-8") as f:
                m_data = json.load(f)
        except Exception as e:
            print(f"Error reading {master_file}: {e}")
            continue
            
        old_id = m_data.get("master_id")
        if not old_id or not (old_id.startswith("MST-") or old_id.startswith("MASTER-")):
            # Fallback - check filename
            filename = master_file.name
            if "MST-" in filename:
                old_id = filename.split("master_")[1].replace(".json", "")
            elif "MASTER-" in filename:
                old_id = filename.split("master_")[1].replace(".json", "")
            else:
                continue

        print(f"Found old master: {old_id} in {inv_dir}")
        
        new_id = indexer.generate_usi_id("IM")
        print(f"  -> Migrating to new ID: {new_id}")
        
        # 1. Update master file content
        m_data["master_id"] = new_id
        
        # Determine new filename
        prefix = "inv_master_" if master_file.name.startswith("inv_master_") else "master_"
        new_master_file = inv_dir / f"{prefix}{new_id}.json"
        
        # Write to new file
        with open(new_master_file, "w", encoding="utf-8") as f:
            json.dump(m_data, f, indent=2, ensure_ascii=False)
            
        # Remove old master file
        master_file.unlink()
        
        # 2. Update all usi_*.json files in this directory
        for usi_file in inv_dir.glob("usi_*.json"):
            try:
                with open(usi_file, "r", encoding="utf-8") as f:
                    u_data = json.load(f)
                    
                if u_data.get("master_id") == old_id:
                    u_data["master_id"] = new_id
                    # Atomic write (as per GEMINI.md)
                    import tempfile
                    fd, temp_path = tempfile.mkstemp(dir=inv_dir, text=True)
                    with os.fdopen(fd, "w", encoding="utf-8") as tf:
                        json.dump(u_data, tf, indent=2, ensure_ascii=False)
                    os.replace(temp_path, usi_file)
                    print(f"  -> Updated {usi_file.name}")
            except Exception as e:
                print(f"Error updating {usi_file}: {e}")

if __name__ == "__main__":
    fix_master_ids()
    print("Done! Pamiętaj o przebudowaniu indeksu (rebuild-index).")
