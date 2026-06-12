from python_worker.adapters import transform_to_unified
import json
from pathlib import Path
p = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata/profbud/osiedle-mocha-tower/raw_oto_4vrJI.json")
raw = json.loads(p.read_text())
res = transform_to_unified("oto", raw)
print(res.get("image_urls")[:2])
