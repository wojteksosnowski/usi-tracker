import sys
from pathlib import Path
from python_worker.config import get_shared_config
from python_worker.developer_manager import DeveloperManager
from python_worker.algorithms.similarity.engine import DeveloperMatcher

config = get_shared_config()
mgr = DeveloperManager(Path(config.public_dir) / "USIdev")
devs = mgr.list_developers()

target = next((d for d in devs if d.get("usi_dev_id") == "DEV-41347"), None)
print("Target:", target["name"], target.get("investments", []))

others = [d for d in devs if d.get("usi_dev_id") != "DEV-41347" and "022" in str(d.get("name", "")).upper()]
for o in others:
    print("Other:", o["usi_dev_id"], o["name"], o.get("investments", []))

matcher = DeveloperMatcher()
sugs = matcher.find_suggestions_for_developer(target, others, {})
print("Suggestions:")
for s in sugs:
    print(s)
