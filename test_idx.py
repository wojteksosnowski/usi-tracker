import sys
from pathlib import Path
sys.path.append("/Volumes/Samsam/claude-py/usi-tracker")
from python_worker.investment_index import get_index

idx = get_index(Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata"))
found = [e for e in idx if e.get("id") == "INV-32316"]
if found:
    entry = found[0]
    print(f"Sources: {entry.get('sources')}")
