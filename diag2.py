import json
from pathlib import Path
from python_worker.detect_similar_devs import normalize_name, fuzzy_match, get_dev_metadata

data_dir = Path("/Volumes/Samsam/Public/USIdata")

slug1 = "4estates-sp-z-o-o"
slug2 = "4estates"

n1 = "4Estates"
n2 = "4Estates"

norm1 = normalize_name(n1)
norm2 = normalize_name(n2)

meta1 = get_dev_metadata(slug1, data_dir)
meta2 = get_dev_metadata(slug2, data_dir)

print(f"Norm1: '{norm1}', Meta1: {meta1}")
print(f"Norm2: '{norm2}', Meta2: {meta2}")

if not norm1 and not meta1 and not set():
    print("D1 skipping")
if not norm2 and not meta2 and not set():
    print("D2 skipping")

if norm1 == norm2:
    print("Match!")

