import os
import glob
from pathlib import Path

def main():
    base_dir = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata")
    count = 0
    for file_path in base_dir.rglob("meta_*_ratings.json"):
        # We need to find the correct portal and portal_id for this directory
        parent = file_path.parent
        usi_files = list(parent.glob("usi_*.json"))
        if not usi_files:
            continue
            
        usi_file = usi_files[0]
        # usi_{portal}_{portal_id}.json
        name_parts = usi_file.stem.split("_")
        if len(name_parts) >= 3:
            portal = name_parts[1]
            portal_id = "_".join(name_parts[2:])
            new_name = f"meta_{portal}_{portal_id}.json"
            new_path = parent / new_name
            os.rename(file_path, new_path)
            print(f"Renamed: {file_path.name} -> {new_name}")
            count += 1
            
    print(f"Total files renamed: {count}")

if __name__ == "__main__":
    main()
