import os
import json
import re
from pathlib import Path
from collections import defaultdict

data_dir = Path("/Volumes/Samsam/Public/USIdata")

errors = []
warnings = []
investments_by_id = defaultdict(list)

def is_archived(filename):
    return bool(re.search(r'_\d{8}_\d{6}\.json$', filename))

def get_expected_canonical_name(inv_slug, data):
    sources = data.get("sources", {})
    if "rp" in sources and sources["rp"].get("id"):
        return f"usi_rp_{sources['rp']['id']}.json"
    elif "oto" in sources and sources["oto"].get("id"):
        return f"usi_oto_{sources['oto']['id']}.json"
    elif "to" in sources and sources["to"].get("id"):
        return f"usi_to_{sources['to']['id']}.json"
    else:
        return f"usi_{inv_slug}.json"

def audit():
    if not data_dir.exists():
        print("Data dir not found")
        return

    for dev_path in data_dir.iterdir():
        if not dev_path.is_dir() or dev_path.name.startswith("_"):
            continue
        
        dev_slug = dev_path.name
        for inv_path in dev_path.iterdir():
            if not inv_path.is_dir():
                continue
                
            inv_slug = inv_path.name
            
            all_usi_files = list(inv_path.glob("usi_*.json"))
            raw_files = list(inv_path.glob("raw_*.json"))
            active_raw = [r for r in raw_files if not is_archived(r.name)]
            
            if not all_usi_files:
                errors.append(f"[{dev_slug}/{inv_slug}] Missing: No usi_*.json file found")
                continue
            
            # Check for multiple active raw files for the same portal
            portal_counts = defaultdict(int)
            for r in active_raw:
                if r.name.startswith("raw_rp"): portal_counts["rp"] += 1
                elif r.name.startswith("raw_oto"): portal_counts["oto"] += 1
                elif r.name.startswith("raw_to"): portal_counts["to"] += 1
            
            for p, count in portal_counts.items():
                if count > 1:
                    errors.append(f"[{dev_slug}/{inv_slug}] Duplication: Multiple active raw_{p} files found ({count})")

            # Check Schema and Naming of ALL usi files
            for usi_file in all_usi_files:
                try:
                    with open(usi_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # Naming check
                        expected = get_expected_canonical_name(inv_slug, data)
                        if usi_file.name != expected:
                            errors.append(f"[{dev_slug}/{inv_slug}] Naming: Expected {expected} but found {usi_file.name}")
                            
                        # Schema check
                        if "usi_inv_id" not in data:
                            errors.append(f"[{dev_slug}/{inv_slug}] Schema: Missing usi_inv_id in {usi_file.name}")
                        else:
                            uid = data["usi_inv_id"]
                            if uid:
                                investments_by_id[uid].append(f"{dev_slug}/{inv_slug}/{usi_file.name}")
                                
                except Exception as e:
                    errors.append(f"[{dev_slug}/{inv_slug}] Corrupted JSON in {usi_file.name}: {e}")

    # Find duplicates
    for uid, paths in investments_by_id.items():
        if len(paths) > 1:
            errors.append(f"Duplicate usi_inv_id {uid} found in: {', '.join(paths)}")
            
    with open("audit_report.json", "w") as f:
        json.dump({"errors": errors, "warnings": warnings, "total_investments": sum(len(p) for p in investments_by_id.values())}, f, indent=2)
    print("Audit finished. See audit_report.json")

if __name__ == "__main__":
    audit()
