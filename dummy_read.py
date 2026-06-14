import json
from pathlib import Path

path = Path("Public/USIdev/022-investments/usi_dev_rp_10788.json")
if path.exists():
    with open(path, "r") as f:
        print(f.read())
