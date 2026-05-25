import os
import json
import re
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Paths
USI_DATA_DIR = Path("/Volumes/Samsam/Public/USIdata")

def extract_hash_from_slug(slug_or_url):
    """Returns hash part from something like 'name-ID4fS6R' or '.../ID4fS6R'."""
    if not slug_or_url:
        return None
    
    # Try -ID prefix first (most common)
    match = re.search(r'-ID([A-Za-z0-9]+)', str(slug_or_url))
    if match:
        return match.group(1)
    
    # Try ID prefix without dash
    match = re.search(r'ID([A-Za-z0-9]+)', str(slug_or_url))
    if match:
        return match.group(1)
        
    return None

def migrate():
    count = 0
    renamed = 0
    
    # Find all usi_oto_*.json files
    for usi_file in USI_DATA_DIR.rglob("usi_oto_*.json"):
        # Check if ID in filename is numeric
        # Filename format: usi_oto_{id}.json
        match = re.match(r"usi_oto_(\d+)\.json", usi_file.name)
        if not match:
            # Already non-numeric or doesn't match expected pattern
            continue
            
        old_id = match.group(1)
        
        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Extract hash ID from internal data
            oto_source = data.get("sources", {}).get("oto", {})
            url = oto_source.get("url")
            slug = data.get("investment_slug")
            
            new_id = extract_hash_from_slug(slug) or extract_hash_from_slug(url)
            
            if not new_id:
                logger.warning(f"Could not extract hash ID for {usi_file}. Slug={slug}, URL={url}")
                continue
                
            if new_id == old_id:
                logger.info(f"ID {old_id} is already what we want? Skipping.")
                continue

            logger.info(f"Migrating {usi_file}: {old_id} -> {new_id}")
            
            # 1. Update internal ID
            if "sources" in data and "oto" in data["sources"]:
                data["sources"]["oto"]["id"] = new_id
            
            # 2. Update filename and save
            new_filename = f"usi_oto_{new_id}.json"
            new_usi_path = usi_file.parent / new_filename
            
            # 3. Handle meta file
            old_meta_name = f"meta_oto_{old_id}.json"
            new_meta_name = f"meta_oto_{new_id}.json"
            old_meta_path = usi_file.parent / old_meta_name
            new_meta_path = usi_file.parent / new_meta_name
            
            # Save updated USI file
            with open(new_usi_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Rename/Move meta file if exists
            if old_meta_path.exists():
                os.rename(old_meta_path, new_meta_path)
                logger.info(f"  Renamed meta: {old_meta_name} -> {new_meta_name}")
            
            # Delete old USI file
            usi_file.unlink()
            
            renamed += 1
            
        except Exception as e:
            logger.error(f"Error migrating {usi_file}: {e}")
            
        count += 1

    logger.info(f"Migration complete. Scanned {count} Otodom files, renamed {renamed}.")

if __name__ == "__main__":
    if not USI_DATA_DIR.exists():
        logger.error(f"Data directory {USI_DATA_DIR} does not exist!")
    else:
        migrate()
