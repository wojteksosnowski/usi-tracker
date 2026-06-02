import pytest
import json
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from python_worker.adapters import RPAdapter, OtodomAdapter, TOAdapter, _get_val, PORTAL_MAPPING

logger = logging.getLogger(__name__)

def get_raw_files():
    """Recursively finds all raw_*.json files in USI_DATA_DIR."""
    if not USI_DATA_DIR.exists():
        return []
    
    # We look for raw_rp_*.json, raw_oto_*.json, raw_to_*.json
    # These are usually inside subdirectories of USI_DATA_DIR
    files = []
    for portal in ["rp", "oto", "to"]:
        files.extend(list(USI_DATA_DIR.glob(f"**/raw_{portal}_*.json")))
    return files

@pytest.mark.skipif(not USI_DATA_DIR.exists(), reason="USI_DATA_DIR not accessible")
def test_all_raw_files_extraction():
    """
    Mass regression test: verifies if all raw files on disk can be successfully
    parsed by the current adapters/mappings.
    """
    raw_files = get_raw_files()
    if not raw_files:
        pytest.skip("No raw files found in USI_DATA_DIR")

    errors = []
    processed_count = 0
    
    for file_path in raw_files:
        portal = None
        if "raw_rp_" in file_path.name:
            adapter = RPAdapter
            portal = "rp"
        elif "raw_oto_" in file_path.name:
            adapter = OtodomAdapter
            portal = "oto"
        elif "raw_to_" in file_path.name:
            adapter = TOAdapter
            portal = "to"
        else:
            continue

        cfg = PORTAL_MAPPING.get(portal, {}).get("investment", {})

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            # Skip "FoundAds" or other collection-type files that might be on disk
            # as they are not meant for individual investment extraction
            if isinstance(raw_data, dict) and raw_data.get("__typename") in ["FoundAds", "AdvertsPages"]:
                continue
            
            # Extract slugs from parent directory or name if possible for context
            inv_slug = file_path.parent.name
            dev_slug = file_path.parent.parent.name if file_path.parent.parent.name != USI_DATA_DIR.name else "unknown"
            
            # Strictly use technical IDs from mapping for validation
            usi_id = _get_val(raw_data, cfg.get("id"))
            
            result = adapter.transform(raw_data, inv_slug, dev_slug)
            
            # Validation based on mapping consistency
            if not usi_id:
                errors.append(f"{file_path}: Missing technical ID (mapping: {cfg.get('id')})")
            
            if not result.get("name"):
                errors.append(f"{file_path}: Extraction returned empty name (mapping: {cfg.get('name')})")
            
            processed_count += 1
            if processed_count % 1000 == 0:
                print(f"Processed {processed_count}/{len(raw_files)} files...")
            
        except Exception as e:
            errors.append(f"{file_path}: {type(e).__name__}: {str(e)}")

    # Print summary if there are errors
    if errors:
        print(f"\nExtraction failed for {len(errors)} out of {processed_count + len(errors)} files:")
        for err in errors[:50]: # Limit output
            print(f"  - {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more errors.")
            
    assert not errors, f"Found {len(errors)} extraction errors in {processed_count + len(errors)} files. See stdout for details."
    print(f"\nSuccessfully processed {processed_count} raw files.")
