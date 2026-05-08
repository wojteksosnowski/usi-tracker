import sys
import json
import os
from pathlib import Path

# Add paths to both projects
TRACKER_PATH = "/Volumes/Samsam/claude-py/usi-tracker"
SCRAPERS_PATH = "/Volumes/Samsam/claude-py/usi-scrapers"

sys.path.insert(0, TRACKER_PATH)
sys.path.insert(0, SCRAPERS_PATH)

from python_worker.adapters.rp import RPAdapter as LegacyRPAdapter
from usi_scrapers.adapters.rp import RPAdapter as LibraryRPAdapter

from python_worker.adapters.otodom import OtodomAdapter as LegacyOtoAdapter
from usi_scrapers.adapters.otodom import OtodomAdapter as LibraryOtoAdapter

from python_worker.adapters.to import TOAdapter as LegacyTOAdapter
from usi_scrapers.adapters.to import TOAdapter as LibraryTOAdapter

def compare_dicts(d1, d2, path=""):
    # Special case: ignore last_sync
    if "last_sync" in path: return True
    
    if type(d1) != type(d2):
        print(f"Type mismatch at {path}: {type(d1)} != {type(d2)}")
        return False
    
    if isinstance(d1, dict):
        for k in set(d1.keys()) | set(d2.keys()):
            if k not in d1:
                print(f"Missing key in d1: {path}.{k}")
                return False
            if k not in d2:
                print(f"Missing key in d2: {path}.{k}")
                return False
            if not compare_dicts(d1[k], d2[k], f"{path}.{k}"):
                return False
    elif isinstance(d1, list):
        if len(d1) != len(d2):
            print(f"Length mismatch at {path}: {len(d1)} != {len(d2)}")
            if "image_urls" in path:
                print(f"  Legacy examples: {d1[:2]}")
                print(f"  Library examples: {d2[:2]}")
            return False
        for i in range(len(d1)):
            if not compare_dicts(d1[i], d2[i], f"{path}[{i}]"):
                return False
    else:
        if d1 != d2:
            print(f"Value mismatch at {path}: {d1!r} != {d2!r}")
            return False
    return True

print("--- PARITY TESTING ---")

# 1. RP Test
try:
    rp_file = "Public/USIdata/022-investments/szalasa-3-warszawa-tarchomin/raw_rp_szalasa-3-warszawa-tarchomin.json"
    with open(rp_file) as f:
        raw_data = json.load(f)
    legacy_out = LegacyRPAdapter.transform(raw_data, "szalasa-3", "022-investments")
    library_out = LibraryRPAdapter.transform(raw_data, "szalasa-3", "022-investments")
    if compare_dicts(legacy_out, library_out):
        print("RP: PASSED")
    else:
        print("RP: FAILED")
except Exception as e:
    print(f"RP: ERROR - {e}")

# 2. Otodom Test
try:
    oto_file = "Public/USIdata/022-investments/szalasa-5/raw_oto_szalasa-5_imported.json"
    with open(oto_file) as f:
        raw_data = json.load(f)
    legacy_out = LegacyOtoAdapter.transform(raw_data, "szalasa-5", "022-investments")
    library_out = LibraryOtoAdapter.transform(raw_data, "szalasa-5", "022-investments")
    if compare_dicts(legacy_out, library_out):
        print("Otodom: PASSED")
    else:
        print("Otodom: FAILED")
except Exception as e:
    print(f"Otodom: ERROR - {e}")

# 3. Tabela Ofert Test
try:
    # Need to find a TO file
    to_files = [f for f in Path("Public/USIdata").rglob("raw_to_*.json")]
    if to_files:
        to_file = to_files[0]
        with open(to_file) as f:
            raw_data = json.load(f)
        # Extract slugs from path
        parts = to_file.parts
        inv_slug = parts[-2]
        dev_slug = parts[-3]
        legacy_out = LegacyTOAdapter.transform(raw_data, inv_slug, dev_slug)
        library_out = LibraryTOAdapter.transform(raw_data, inv_slug, dev_slug)
        if compare_dicts(legacy_out, library_out):
            print("TabelaOfert: PASSED")
        else:
            print("TabelaOfert: FAILED")
            from usi_scrapers.utils.images import clean_filename
            from python_worker.scraper_to import _cdn_filename
            
            raw_urls = raw_data.get("_raw_gallery_urls", [])
            leg_map = {}
            lib_map = {}
            for u in raw_urls:
                leg_map[u] = _cdn_filename(u)
                lib_map[u] = clean_filename(u)
            
            # Find a case where clean_filename is same but _cdn_filename is different
            found = False
            for u1 in raw_urls:
                for u2 in raw_urls:
                    if u1 == u2: continue
                    if lib_map[u1] == lib_map[u2] and leg_map[u1] != leg_map[u2]:
                        print(f"DEDUPLICATION DISCREPANCY FOUND:")
                        print(f"  URL 1: {u1}")
                        print(f"  URL 2: {u2}")
                        print(f"  Legacy: {leg_map[u1]} != {leg_map[u2]}")
                        print(f"  Library: {lib_map[u1]} == {lib_map[u2]}")
                        found = True
                        break
                if found: break
    else:
        print("TabelaOfert: SKIPPED (no data)")
except Exception as e:
    print(f"TabelaOfert: ERROR - {e}")
