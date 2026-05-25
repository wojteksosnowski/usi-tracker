import os
import json
import re
import logging
from pathlib import Path
from collections import defaultdict
from python_worker.config import USI_DEV_DIR

# Simple logger for CLI output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("audit_usidev")

def audit():
    dev_dir = Path(USI_DEV_DIR)
    if not dev_dir.exists():
        logger.error(f"Error: USIdev directory not found at {dev_dir}")
        return

    errors = []
    warnings = []
    stats = defaultdict(int)

    logger.info(f"Starting USIdev audit in {dev_dir}...")

    # Iterate over developer folders
    for dev_path in sorted(dev_dir.iterdir()):
        if not dev_path.is_dir() or dev_path.name.startswith("_"):
            continue
            
        dev_slug = dev_path.name
        stats["total_dev_folders"] += 1
        
        usi_files = list(dev_path.glob("usi_dev_*.json"))
        master_file = next(dev_path.glob("dev_master_*.json"), None)
        raw_files = {f.name for f in dev_path.glob("raw_*.json")}
        
        active_ids = set()

        # 1. Validate Level 2 records (usi_dev_*.json)
        for usi_file in usi_files:
            if usi_file.name.startswith("dev_master_"): continue
            stats["total_l2_files"] += 1
            
            try:
                with open(usi_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                usi_id = data.get("usi_dev_id")
                if not usi_id:
                    errors.append(f"[{dev_slug}] Missing usi_dev_id in {usi_file.name}")
                    continue
                
                active_ids.add(usi_id)
                
                # Rule A: Canonical Naming
                expected_name = f"usi_dev_{usi_id}_{dev_slug}.json"
                if usi_file.name != expected_name:
                    errors.append(f"[{dev_slug}] Naming: Expected {expected_name} but found {usi_file.name}")
                
                # Rule B: 1:1 Portal Rule
                pm = data.get("portal_mapping", {})
                active_portals = [p for p in ("rp", "oto", "to") if pm.get(p)]
                if len(active_portals) > 1:
                    errors.append(f"[{dev_slug}/{usi_id}] 1:1 Violation: File has multiple portals: {active_portals}")
                elif len(active_portals) == 0:
                    warnings.append(f"[{dev_slug}/{usi_id}] Orphan: File has no active portal mapping")
                
                # Rule C: Raw File Integrity
                if "raw_file" not in data:
                    errors.append(f"[{dev_slug}/{usi_id}] Missing raw_file field")
                else:
                    rf_name = data.get("raw_file")
                    if rf_name:
                        if rf_name not in raw_files:
                            errors.append(f"[{dev_slug}/{usi_id}] Broken Link: raw_file '{rf_name}' does not exist on disk")
                    else:
                        # Optional warning if someone thinks every L2 MUST have a raw file
                        if active_portals:
                            warnings.append(f"[{dev_slug}/{usi_id}] No raw_file linked despite having active portal")

            except Exception as e:
                errors.append(f"[{dev_slug}] Corrupted JSON or read error in {usi_file.name}: {e}")

        # 2. Validate Level 3 records (dev_master_*.json)
        if master_file:
            stats["total_master_files"] += 1
            try:
                with open(master_file, "r", encoding="utf-8") as f:
                    m_data = json.load(f)
                
                # Check Master ID link
                mid = m_data.get("master_usi_dev_id")
                if mid not in active_ids:
                    errors.append(f"[{dev_slug}] Master link broken: master_usi_dev_id '{mid}' has no corresponding L2 file")
                
                # Check Merged Members links
                for member in m_data.get("merged_from", []):
                    cid = member.get("usi_dev_id")
                    if cid and cid not in active_ids:
                        errors.append(f"[{dev_slug}] Member link broken: merged child '{cid}' has no corresponding L2 file")
                        
            except Exception as e:
                errors.append(f"[{dev_slug}] Corrupted Master JSON in {master_file.name}: {e}")

    # Final Report
    report = {
        "summary": {
            "total_dev_folders": stats["total_dev_folders"],
            "total_l2_files": stats["total_l2_files"],
            "total_master_files": stats["total_master_files"],
            "total_errors": len(errors),
            "total_warnings": len(warnings)
        },
        "errors": errors,
        "warnings": warnings
    }

    report_path = Path("audit_usidev_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("\nAudit Finished!")
    logger.info(f"  Folders scanned: {stats['total_dev_folders']}")
    logger.info(f"  Errors found:    {len(errors)}")
    logger.info(f"  Warnings found:  {len(warnings)}")
    logger.info(f"  Report saved to: {report_path}")

if __name__ == "__main__":
    audit()
