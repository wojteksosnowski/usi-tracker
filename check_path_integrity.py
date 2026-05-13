import os
import json
from pathlib import Path
import sys

# Ensure we can import from python_worker
sys.path.append(os.getcwd())
try:
    from python_worker import config
except ImportError as e:
    print(f"Error importing config: {e}")
    sys.exit(1)

def check_path_integrity():
    data_dir = Path(config.USI_DATA_DIR)
    
    total_inv_files = 0
    path_mismatches = 0
    slug_mismatches = []
    
    # Filter only investment files (usi_*.json that are NOT usi_dev_*.json)
    json_files = [f for f in data_dir.rglob("usi_*.json") if "usi_dev_" not in f.name]
    total_inv_files = len(json_files)
    print(f"Auditing {total_inv_files} INVESTMENT files for slug/path integrity...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
            
        dev_slug = data.get("developer_slug")
        inv_slug = data.get("investment_slug")
        
        if not dev_slug or not inv_slug:
            path_mismatches += 1
            slug_mismatches.append(f"MISSING SLUGS: {json_file.relative_to(data_dir)}")
            continue
            
        rel_parts = json_file.relative_to(data_dir).parts
        
        # Expected: (dev_slug, inv_slug, usi_inv_slug.json)
        if len(rel_parts) < 3:
            path_mismatches += 1
            slug_mismatches.append(f"SHALLOW PATH: {json_file.relative_to(data_dir)} (parts: {rel_parts})")
            continue
            
        actual_inv_folder = rel_parts[-2]
        actual_dev_folder = rel_parts[-3]
        
        mismatch_reason = []
        if actual_inv_folder != inv_slug:
            mismatch_reason.append(f"inv_slug mismatch: folder='{actual_inv_folder}' vs json='{inv_slug}'")
        if actual_dev_folder != dev_slug:
            mismatch_reason.append(f"dev_slug mismatch: folder='{actual_dev_folder}' vs json='{dev_slug}'")
            
        if mismatch_reason:
            path_mismatches += 1
            slug_mismatches.append(f"MISMATCH: {json_file.relative_to(data_dir)} -> {', '.join(mismatch_reason)}")

    print("\n--- INTEGRITY RESULTS (INVESTMENTS ONLY) ---")
    print(f"Total investment files checked: {total_inv_files}")
    print(f"Files with path/slug mismatches: {path_mismatches}")
    
    if slug_mismatches:
        print("\nExamples of mismatches (first 20):")
        for m in slug_mismatches[:20]:
            print(f"- {m}")

if __name__ == "__main__":
    check_path_integrity()
