import sys
import os
from pathlib import Path
import inspect
import json

# Setup path
_BASE_DIR = Path.cwd()
sys.path.insert(0, str(_BASE_DIR))
lib_path = str(_BASE_DIR.parent / "usi-scrapers")
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

def dump_api():
    try:
        import usi_scrapers
        from usi_scrapers import api as scraper_api
        
        print(f"Library Version: {getattr(usi_scrapers, '__version__', 'N/A')}")
        
        print("\n--- usi_scrapers.api methods ---")
        # Filter for functions defined in the api module, not imported ones
        for name, obj in inspect.getmembers(scraper_api):
            if inspect.isfunction(obj) and obj.__module__.endswith('.api'):
                sig = inspect.signature(obj)
                print(f"{name}{sig}")
                
        from usi_scrapers.fetcher import Fetcher
        print("\n--- usi_scrapers.fetcher.Fetcher methods ---")
        for name, obj in inspect.getmembers(Fetcher):
            if inspect.isfunction(obj) and not name.startswith('__'):
                sig = inspect.signature(obj)
                print(f"{name}{sig}")
                
    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    dump_api()
