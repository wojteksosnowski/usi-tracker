import csv
import logging
import shutil
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("SyncImages")

def sync_images(csv_path: Path, usi_dir: Path):
    konkurenci_path = csv_path.parent / "Konkurenci.csv"
    
    # 1. Build Developer Lookup
    dev_lookup = {}
    if konkurenci_path.exists():
        with open(konkurenci_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                d_name = row.get('Deweloper', '').strip()
                d_slug = row.get('usiFolder', '').strip()
                if d_name and d_slug:
                    dev_lookup[d_name] = d_slug

    from python_worker.csv_importer import slugify

    # 2. Build mapping: filename -> correct target directory
    file_to_target_dir = {}
    logger.info("Building filename mapping from USImaster.csv...")
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inv_slug = row.get('USIfolder', '').strip()
            if not inv_slug: continue
            
            dev_name = row.get('Deweloper', '').strip()
            dev_slug = dev_lookup.get(dev_name)
            if not dev_slug:
                dev_slug = slugify(dev_name) if dev_name else "unknown"
                
            target_dir = usi_dir / dev_slug / inv_slug
            
            img_list_raw = row.get('imgList', '')
            if img_list_raw:
                # Pliki często rozdzielone przecinkami np. /Public/USI/.../img1.jpg, /Public/USI/.../img2.jpg
                paths = [p.strip() for p in img_list_raw.split(',') if p.strip()]
                for p in paths:
                    filename = p.split('/')[-1]
                    if filename:
                        file_to_target_dir[filename] = target_dir

    logger.info(f"Registered {len(file_to_target_dir)} unique filenames from database.")

    # 3. Scan existing files and move them if necessary
    logger.info(f"Scanning physical files in {usi_dir}...")
    moved_count = 0
    skipped_count = 0
    unmapped_count = 0
    
    for root, _, files in os.walk(usi_dir):
        root_path = Path(root)
        for file in files:
            if file.startswith('.'): continue
            
            current_path = root_path / file
            target_dir = file_to_target_dir.get(file)
            
            if target_dir:
                target_path = target_dir / file
                if current_path != target_path:
                    # Need to move
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(current_path), str(target_path))
                    moved_count += 1
                else:
                    # Already in correct place
                    skipped_count += 1
            else:
                unmapped_count += 1

    logger.info(f"Moved {moved_count} files to correct directories.")
    logger.info(f"Skipped {skipped_count} files (already in correct place).")
    logger.info(f"Found {unmapped_count} files not present in database.")

    # 4. Clean up empty directories
    logger.info("Cleaning up empty directories...")
    deleted_count = 0
    for root, dirs, _ in os.walk(usi_dir, topdown=False):
        for name in dirs:
            dir_path = Path(root) / name
            try:
                # rmdir will fail if directory is not empty
                dir_path.rmdir()
                deleted_count += 1
            except OSError:
                pass
                
    logger.info(f"Deleted {deleted_count} empty directories.")

from python_worker.config import PUBLIC_USI_DIR, CSV_PATH

if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser(description="Synchronize image paths based on database filenames")
    args = parser.parse_args()
    
    usi_dir = PUBLIC_USI_DIR
    
    sync_images(CSV_PATH, usi_dir)
