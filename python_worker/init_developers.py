import csv
import logging
import argparse
import sys
from pathlib import Path

# Add parent directory to sys.path to allow imports when running as script
sys.path.append(str(Path(__file__).parent.parent))

from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR, DROPBOX_PATH

logger = logging.getLogger("InitDevelopers")
logging.basicConfig(level=logging.INFO)

def import_developers_from_csv(csv_path: str | Path, data_dir: Path):
    """
    Imports developer mappings from Konkurenci.csv and creates usi_dev_{slug}.json files.
    """
    manager = DeveloperManager(data_dir)
    count = 0
    
    csv_path = Path(csv_path)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return 0

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dev_slug = row.get('usiFolder', '').strip()
            name = row.get('Deweloper', '').strip()
            
            if not dev_slug or not name:
                continue
                
            rp_id = row.get('rpID', '').strip()
            rp_slug = row.get('rpSlug', '').strip()
            oto_id_raw = row.get('otoID', '').strip()
            oto_url = row.get('otoWWW', '').strip()
            website = row.get('www', '').strip()
            
            # Extract numeric ID from 'ID8495786'
            oto_agency_ids = []
            if oto_id_raw.startswith('ID'):
                try:
                    oto_agency_ids.append(int(oto_id_raw[2:]))
                except ValueError:
                    pass
            elif oto_id_raw.isdigit():
                 oto_agency_ids.append(int(oto_id_raw))

            dev_data = {
                "developer_slug": dev_slug,
                "name": name,
                "website": website if website else None,
                "portal_mapping": {
                    "rp": {},
                    "oto": {},
                    "to": {}
                }
            }
            
            if rp_id:
                dev_data["portal_mapping"]["rp"]["id"] = rp_id
            if rp_slug:
                dev_data["portal_mapping"]["rp"]["slug"] = rp_slug
                
            if oto_agency_ids:
                dev_data["portal_mapping"]["oto"]["agency_ids"] = oto_agency_ids
            if oto_url:
                dev_data["portal_mapping"]["oto"]["url"] = oto_url
                
            # Check for TabelaOfert slug in otoSlug if it contains 'tabelaofert' or something?
            # Actually Konkurenci.csv doesn't seem to have TO-specific slug column yet.
            # But we can add it later.
            
            manager.create_developer_file(dev_data)
            count += 1
            
    logger.info(f"Successfully imported {count} developers from {csv_path}")
    return count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize developer database from Konkurenci.csv")
    parser.add_argument("--csv", default="reference-data/coda/Konkurenci.csv", help="Path to Konkurenci.csv")
    parser.add_argument("--data-dir", help="Path to USIdata directory (overrides config)")
    
    args = parser.parse_args()
    
    target_data_dir = Path(args.data_dir) if args.data_dir else USI_DATA_DIR
    
    logger.info(f"Initializing developers in: {target_data_dir}")
    import_developers_from_csv(args.csv, target_data_dir)
