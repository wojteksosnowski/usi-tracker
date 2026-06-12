import json
from pathlib import Path

path = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata/unknown/osiedle-mocha-tower/usi_to_4vrJI.json")
if path.exists():
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["usi_inv_id"] = "oto_4vrJI"
    if "to" in data.get("sources", {}):
        data["sources"]["oto"] = data["sources"].pop("to")
        
    new_path = path.parent / "usi_oto_4vrJI.json"
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    path.unlink()
    print("Fixed JSON and renamed.")
