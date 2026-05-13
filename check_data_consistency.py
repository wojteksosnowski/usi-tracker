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
    
    print(f"Checking data in: {data_dir}")
    print(f"Checking images in: {public_usi_dir}")
    
    investments_with_ratings = 0
    investments_with_missing_photos = 0
    missing_paths_examples = []
    
    # Recursively find all usi_*.json files
    json_files = list(data_dir.rglob("usi_*.json"))
    print(f"Found {len(json_files)} unified JSON files.")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
            continue
            
        ratings = data.get("ratings", {})
        # Check if any rating is not None
        has_rating = any(v is not None for k, v in ratings.items() if k != "komentarz") or ratings.get("komentarz")
        
        if has_rating:
            investments_with_ratings += 1
            image_paths = data.get("assets", {}).get("image_paths", [])
            
            missing_in_this_inv = []
            for img_path in image_paths:
                # image_paths are usually relative to Public/USI/ (the assets folder)
                # or absolute if they start with /
                full_path = public_usi_dir / img_path
                if not full_path.exists():
                    missing_in_this_inv.append(img_path)
            
            if missing_in_this_inv and (len(image_paths) > 0):
                investments_with_missing_photos += 1
                if len(missing_paths_examples) < 5:
                    missing_paths_examples.append({
                        "file": str(json_file.relative_to(data_dir)),
                        "missing_count": len(missing_in_this_inv),
                        "total_count": len(image_paths),
                        "sample_missing": missing_in_this_inv[:2]
                    })
            elif not image_paths and has_rating:
                # Case where it has ratings but images_count is 0 or list is empty
                investments_with_missing_photos += 1
                if len(missing_paths_examples) < 5:
                    missing_paths_examples.append({
                        "file": str(json_file.relative_to(data_dir)),
                        "missing_count": "ALL (empty list)",
                        "total_count": 0,
                        "sample_missing": []
                    })

    print("\n--- RESULTS ---")
    print(f"Total investments with ratings: {investments_with_ratings}")
    print(f"Investments with ratings but MISSING/EMPTY photos: {investments_with_missing_photos}")
    
    if missing_paths_examples:
        print("\nExamples of affected investments:")
        for ex in missing_paths_examples:
            print(f"- {ex['file']}: {ex['missing_count']}/{ex['total_count']} missing. Examples: {ex['sample_missing']}")

if __name__ == "__main__":
    check_investments()
