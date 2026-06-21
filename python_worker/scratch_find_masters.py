from pathlib import Path
import json

data_dir = Path("Public/USIdata")
for p in data_dir.rglob("master_*.json"):
    print(p)
for p in data_dir.rglob("inv_master_*.json"):
    print(p)
