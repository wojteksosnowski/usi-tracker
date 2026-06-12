import json
from pathlib import Path
p = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata/unknown/osiedle-centrum-park-mickiewicza-44-45-legnica-mieszkania-na-sprzedaz/usi_to_9155247.json")
data = json.loads(p.read_text())
data["usi_inv_id"] = "to_9155247"
p.write_text(json.dumps(data, indent=2))
