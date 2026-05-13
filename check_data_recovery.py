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

def check_investments():
    data_dir = Path(config.USI_DATA_DIR)
    public_usi_dir = Path(config.PUBLIC_USI_DIR)
    
    investments_with_ratings = 0
    missing_assets_in_usi = 0
    recoverable_from_app_result = 0
    actually_missing_on_disk = 0
    
    json_files = list(data_dir.rglob("usi_*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
            
        ratings = data.get("ratings", {})
        has_rating = any(v is not None for k, v in ratings.items() if k != "komentarz") or ratings.get("komentarz")
        
        if has_rating:
            investments_with_ratings += 1
            assets = data.get("assets", {})
            image_paths = assets.get("image_paths", [])
            
            if not assets or not image_paths:
                missing_assets_in_usi += 1
                
                # Check if we can recover from app_result_imported.json
                app_result_path = json_file.parent / "app_result_imported.json"
                if app_result_path.exists():
                    try:
                        with open(app_result_path, 'r', encoding='utf-8') as f:
                            app_data = json.load(f)
                        app_images = app_data.get("image_paths", [])
                        if app_images:
                            recoverable_from_app_result += 1
                            # Check if at least the first one exists on disk
                            # Note: app_result_imported.json might have /Public/USI/ prefix
                            first_img = app_images[0]
                            if first_img.startswith("/Public/USI/"):
                                # Strip the prefix to check against PUBLIC_USI_DIR
                                rel_path = first_img.replace("/Public/USI/", "", 1)
                                full_path = public_usi_dir / rel_path
                            else:
                                full_path = public_usi_dir / first_img
                                
                            if not full_path.exists():
                                actually_missing_on_disk += 1
                    except: pass

    print(f"Total with ratings: {investments_with_ratings}")
    print(f"Missing 'assets' in usi_*.json: {missing_assets_in_usi}")
    print(f"Recoverable from app_result_imported.json: {recoverable_from_app_result}")
    print(f"Actually missing on disk (first image check): {actually_missing_on_disk}")

if __name__ == "__main__":
    check_investments()
