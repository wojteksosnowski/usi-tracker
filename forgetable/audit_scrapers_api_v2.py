import sys
import os
from pathlib import Path
import inspect

# Setup path
_BASE_DIR = Path.cwd()
sys.path.insert(0, str(_BASE_DIR))
lib_path = str(_BASE_DIR.parent / "usi-scrapers")
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

def dump_api():
    try:
        from usi_scrapers import api as scraper_api
        
        print("\n--- ALL usi_scrapers.api members ---")
        for name, obj in inspect.getmembers(scraper_api):
            if inspect.isfunction(obj):
                sig = inspect.signature(obj)
                print(f"{name}{sig}  [from {obj.__module__}]")
                
    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    dump_api()
