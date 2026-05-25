import json
from pathlib import Path
from collections import defaultdict
data_dir = Path("Public/USIdata")
inv_folders = defaultdict(list)
for usi_file in data_dir.rglob("usi_*.json"):
    if "usi_dev_" in usi_file.name: continue
    inv_folders[usi_file.parent].append(usi_file)
print(f"Total files: {sum(len(files) for files in inv_folders.values())}")
print(f"Total unique folders: {len(inv_folders)}")
