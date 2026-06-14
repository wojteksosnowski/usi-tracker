import pytest
import json
from pathlib import Path
from python_worker.daemons import TrackerDoktorDelegate
from python_worker.developer_index import rebuild as rebuild_index

dev_dir = Path("tmp_USIdev")
inv_dir = Path("tmp_USIdata")
dev_dir.mkdir(parents=True, exist_ok=True)
inv_dir.mkdir(parents=True, exist_ok=True)

dev1_slug = "dev-1-slug"
dev1_dir = dev_dir / dev1_slug
dev1_dir.mkdir(exist_ok=True)

dev1_data = {
    "developer_slug": dev1_slug,
    "name": "Super Development",
    "usi_dev_id": "DEV-E2E-001",
    "portal_mapping": {"rp": {"id": "1", "slug": dev1_slug}, "oto": None, "to": None},
    "investments": [{"slug": "dev-1-slug/inv-1"}]
}
with open(dev1_dir / "usi_dev_rp_1.json", "w", encoding="utf-8") as f:
    json.dump(dev1_data, f)

rebuild_index(inv_dir, dev_dir)
delegate = TrackerDoktorDelegate(inv_dir, dev_dir)
sugs = [{"target_id": "DEV-E2E-002", "target_slug": "dev-2", "reason": "foo", "score": 1.0}]
delegate.save_suggestions("DEV-E2E-001", sugs)
with open(dev1_dir / "usi_dev_rp_1.json", "r") as f:
    print(f.read())
