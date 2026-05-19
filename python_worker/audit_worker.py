"""
audit_worker.py — CLI tool to process investments flagged for audit.
"""
import json
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scan_for_audits():
    data_root = Path(USI_DATA_DIR)
    if not data_root.exists():
        logger.error(f"Data directory {data_root} does not exist.")
        return

    flagged = []
    for dev_dir in data_root.iterdir():
        if not dev_dir.is_dir() or dev_dir.name == "reports":
            continue
        
        for inv_dir in dev_dir.iterdir():
            if not inv_dir.is_dir():
                continue
            
            usi_files = list(inv_dir.glob("usi_*.json"))
            if not usi_files:
                continue
            
            # Assume one usi_ file per investment dir
            usi_file = usi_files[0]
            try:
                with open(usi_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                audit_info = data.get("audit", {})
                if audit_info.get("audit_needed"):
                    reports = data.get("issue_reports", [])
                    latest_note = reports[0]["note"] if reports else "No notes"
                    flagged.append({
                        "id": data.get("usi_inv_id"),
                        "name": data.get("name"),
                        "dev": data.get("developer_name"),
                        "note": latest_note,
                        "path": usi_file
                    })
            except Exception as e:
                logger.error(f"Error reading {usi_file}: {e}")

    return flagged

def run_audit_cli():
    print("=== USI Audit Worker ===")
    flagged = scan_for_audits()
    
    if not flagged:
        print("No investments flagged for audit.")
        return

    print(f"Found {len(flagged)} investments needing audit:\n")
    for i, item in enumerate(flagged, 1):
        print(f"{i}. [{item['id']}] {item['name']} ({item['dev']})")
        print(f"   Note: {item['note']}")
        print(f"   File: {item['path']}\n")

    print("Audit processing logic (e.g. re-downloading images, refreshing metadata) goes here.")

if __name__ == "__main__":
    run_audit_cli()
