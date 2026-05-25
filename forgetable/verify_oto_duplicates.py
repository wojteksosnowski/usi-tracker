import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "Public" / "USIdata"

def run_audit():
    # Map OTO ID -> list of folders
    oto_index = defaultdict(list)
    
    # Iterate through folders: Public/USIdata/dev_slug/inv_slug
    # Globbing */* will find all dev/inv folders
    for inv_dir in DATA_DIR.glob("*/*"):
        if not inv_dir.is_dir():
            continue
        
        # Look for any usi_*.json file
        usi_files = list(inv_dir.glob("usi_*.json"))
        if not usi_files:
            continue
            
        for usi_file in usi_files:
            try:
                with open(usi_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                oto_src = data.get("sources", {}).get("oto", {})
                oto_id = oto_src.get("id")
                
                if oto_id:
                    oto_index[str(oto_id)].append(str(inv_dir))
                    
            except Exception as e:
                # print(f"Error reading {usi_file}: {e}")
                continue

    # Identify duplicates
    duplicates = {oid: folders for oid, folders in oto_index.items() if len(set(folders)) > 1}
    
    print(f"Total OTO IDs indexed: {len(oto_index)}")
    print(f"Total OTO-based duplicates: {len(duplicates)}")
    
    for oid, folders in duplicates.items():
        print(f"\nOTO ID: {oid}")
        for folder in set(folders):
            print(f"  {folder}")

if __name__ == "__main__":
    run_audit()
