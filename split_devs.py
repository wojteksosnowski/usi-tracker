import json
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from python_worker.developer_manager import DeveloperManager
from datetime import datetime

logging.basicConfig(level=logging.INFO)

dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
dev_dir = dm.dev_dir

split_count = 0

for dev_file in dev_dir.rglob("usi_dev_*.json"):
    if dev_file.name.startswith("dev_master_"):
        continue

    try:
        with open(dev_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        pm = data.get("portal_mapping", {})
        active_portals = [p for p in ("rp", "oto", "to") if pm.get(p)]

        if len(active_portals) > 1:
            logging.info(f"Splitting {dev_file.name} which has {active_portals}")
            
            kept_portal = active_portals[0]
            
            for other_portal in active_portals[1:]:
                new_id = dm.generate_usi_id("DEV")
                new_data = data.copy()
                new_data["usi_dev_id"] = new_id
                new_pm = {"rp": None, "oto": None, "to": None}
                new_pm[other_portal] = pm[other_portal]
                new_data["portal_mapping"] = new_pm
                
                new_file = dev_file.parent / f"usi_dev_{new_id}_{data.get('developer_slug', 'unknown')}.json"
                with open(new_file, "w", encoding="utf-8") as f_new:
                    json.dump(new_data, f_new, ensure_ascii=False, indent=2)
                logging.info(f"  -> Created {new_file.name} for {other_portal}")
            
            new_pm_orig = {"rp": None, "oto": None, "to": None}
            new_pm_orig[kept_portal] = pm[kept_portal]
            data["portal_mapping"] = new_pm_orig
            
            with open(dev_file, "w", encoding="utf-8") as f_orig:
                json.dump(data, f_orig, ensure_ascii=False, indent=2)
            logging.info(f"  -> Updated original file to keep only {kept_portal}")
            
            split_count += 1
            
    except Exception as e:
        logging.error(f"Error processing {dev_file}: {e}")

logging.info(f"Done. Split {split_count} files.")
