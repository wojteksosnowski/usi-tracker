import json
from pathlib import Path
from python_worker.services.investment_service import InvestmentService

USI_DATA_DIR = Path("/Volumes/Samsam/Public/USIdata")
svc = InvestmentService(data_dir=USI_DATA_DIR)

# Find an investment with multiple anchors (if possible) or just any
# We know aura-mokotow-ii-ID4ug2k has a record. Let's see its USI ID.
# Actually, I can just find any usi_*.json that has a master_id.
count = 0
for p in USI_DATA_DIR.rglob("usi_*.json"):
    if "usi_dev_" in p.name: continue
    data = json.loads(p.read_text())
    if data.get("master_id"):
        print(f"Checking investment {data['usi_inv_id']} which has master_id {data['master_id']}")
        res = svc.get_unified_view(data["usi_inv_id"])
        print(f"Data portals returned: {[d['portal'] for d in res.get('data', [])]}")
        print(f"Merged anchors count in master: {len(res.get('merged_anchors', []))}")
        count += 1
        if count >= 3: break
