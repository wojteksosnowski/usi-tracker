import json
from pathlib import Path
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_index import load as load_dev_index

def audit():
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    devs = load_dev_index(USI_DEV_DIR) or dm.list_developers(only_merged=False)
    
    # Check for devs with no investments
    # We can check if USI_DATA_DIR / dev["developer_slug"] exists and has subdirs
    orphans = []
    schema_issues = []
    
    for dev in devs:
        slug = dev.get("developer_slug")
        if not slug:
            continue
            
        # 1. Check for schema issues
        has_schema_issue = False
        pm = dev.get("portal_mapping")
        if not pm or not isinstance(pm, dict):
            has_schema_issue = True
            schema_issues.append({"id": dev.get("usi_dev_id"), "slug": slug, "reason": "No valid portal_mapping"})
        else:
            has_mapping = False
            for p in ["rp", "oto", "to"]:
                if p in pm and pm[p]:
                    has_mapping = True
            if not has_mapping and not dev.get("master_id"):
                schema_issues.append({"id": dev.get("usi_dev_id"), "slug": slug, "reason": "Empty portal_mapping and no master_id"})
                has_schema_issue = True
        
        # 2. Check for orphans
        dev_data_dir = USI_DATA_DIR / slug
        has_investments = False
        if dev_data_dir.exists() and dev_data_dir.is_dir():
            for child in dev_data_dir.iterdir():
                if child.is_dir() and not child.name.startswith("_") and not child.name.startswith("."):
                    has_investments = True
                    break
                    
        # If it's merged into another dev, it might not have its own folder
        is_merged = bool(dev.get("master_id"))
        
        if not has_investments and not is_merged:
            orphans.append({"id": dev.get("usi_dev_id"), "slug": slug})
            
    print(f"Total Developers Checked: {len(devs)}")
    print(f"Orphans (No investments and not merged): {len(orphans)}")
    if orphans:
        print("First 10 orphans:", orphans[:10])
    
    print(f"\\nSchema Issues: {len(schema_issues)}")
    if schema_issues:
        print("First 10 schema issues:", schema_issues[:10])

if __name__ == "__main__":
    audit()
