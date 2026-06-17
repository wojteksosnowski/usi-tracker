import os
import json
import logging
from pathlib import Path
import sys

# Dodanie katalogu głównego do ścieżki (umożliwia import z python_worker)
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_backfill(data_dir: Path, usi_dir: Path) -> tuple[int, int]:
    count_updated = 0
    count_errors = 0

    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return 0, 0

    for dev_dir in data_dir.iterdir():
        if not dev_dir.is_dir() or dev_dir.name.startswith("_"):
            continue
            
        for inv_dir in dev_dir.iterdir():
            if not inv_dir.is_dir():
                continue
                
            dev_slug = dev_dir.name
            inv_slug = inv_dir.name
            
            for usi_file in inv_dir.glob("usi_*.json"):
                try:
                    with open(usi_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    changed = False
                    
                    # 1. Czyszczenie image_urls z lokalnych ścieżek
                    urls = data.get("image_urls", [])
                    clean_urls = []
                    for url in urls:
                        if isinstance(url, str) and url.startswith("http"):
                            clean_urls.append(url)
                    
                    if len(clean_urls) != len(urls):
                        data["image_urls"] = clean_urls
                        changed = True
                        
                    # 2. Rekonstrukcja image_paths z rzeczywistych plików
                    physical_dir = usi_dir / dev_slug / inv_slug
                    image_paths = []
                    if physical_dir.exists() and physical_dir.is_dir():
                        for item in sorted(physical_dir.iterdir()):
                            if item.is_file() and item.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                                rel_path = f"/Public/USI/{dev_slug}/{inv_slug}/{item.name}"
                                image_paths.append(rel_path)
                                
                    current_paths = data.get("image_paths", [])
                    if image_paths != current_paths:
                        data["image_paths"] = image_paths
                        data["images_count"] = len(image_paths)
                        changed = True
                        
                    if changed:
                        with open(usi_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        count_updated += 1
                        logger.info(f"Updated {dev_slug}/{inv_slug} ({usi_file.name}): {len(image_paths)} local paths restored.")
                        
                except Exception as e:
                    logger.error(f"Error processing {usi_file}: {e}")
                    count_errors += 1

    return count_updated, count_errors

def main():
    data_dir = Path(USI_DATA_DIR)
    usi_dir = Path(PUBLIC_USI_DIR)
    
    logger.info(f"Starting image_paths backfill...")
    logger.info(f"USIdata: {data_dir}")
    logger.info(f"USI: {usi_dir}")
    
    updated, errors = run_backfill(data_dir, usi_dir)
    logger.info(f"Backfill complete. Updated {updated} files. Errors: {errors}")

if __name__ == "__main__":
    main()
