from python_worker.adapters import AdapterFactory
import json
from pathlib import Path
p = Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata/profbud/osiedle-mocha-tower/raw_oto_4vrJI.json")
raw = json.loads(p.read_text())
res = AdapterFactory.get_adapter("oto").transform(raw, "inv", "dev")
print(type(res.get("image_urls")[0]))
print(res.get("image_urls")[:2])
