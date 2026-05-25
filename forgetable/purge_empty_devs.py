import json
import shutil
import logging
import sys
import os
from pathlib import Path

# Add current directory to path so python_worker is discoverable
sys.path.append(os.getcwd())

from python_worker.config import USI_DATA_DIR, USI_DEV_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("PurgeEmptyDevs")

def purge_empty_developers(dry_run=True):
    data_dir = Path(USI_DATA_DIR)
    dev_dir = Path(USI_DEV_DIR)

    if not data_dir.exists() or not dev_dir.exists():
        logger.error("Data or Dev directory does not exist.")
        return

    # 1. Zbierz wszystkich deweloperów z katalogu USIdev
    all_devs = {}
    for dev_path in dev_dir.iterdir():
        if not dev_path.is_dir():
            continue
        
        dev_files = list(dev_path.glob("usi_dev_*_*.json")) or list(dev_path.glob("usi_dev_*.json"))
        if not dev_files:
            # Pusty folder bez pliku usi_dev też do usunięcia
            all_devs[dev_path.name] = {"name": dev_path.name, "is_merged": False, "path": dev_path, "portals": []}
            continue
            
        try:
            data = json.loads(dev_files[0].read_text(encoding="utf-8"))
            is_merged = bool(data.get("parent_id"))
            
            # Ekstrakcja portali z portal_mapping
            mapping = data.get("portal_mapping", {})
            active_portals = [p.upper() for p, val in mapping.items() if val]
            
            all_devs[dev_path.name] = {
                "name": data.get("name", dev_path.name),
                "is_merged": is_merged,
                "path": dev_path,
                "portals": active_portals
            }
        except Exception:
            all_devs[dev_path.name] = {"name": dev_path.name, "is_merged": False, "path": dev_path, "portals": []}
            
    # 2. Zbierz deweloperów, którzy mają przynajmniej 1 inwestycję w USIdata
    active_dev_slugs = set()
    for dev_path in data_dir.iterdir():
        if not dev_path.is_dir():
            continue
            
        has_investments = False
        for inv_path in dev_path.iterdir():
            if not inv_path.is_dir():
                continue
            if any(inv_path.glob("usi_*.json")):
                has_investments = True
                break
                
        if has_investments:
            active_dev_slugs.add(dev_path.name)
            
    # 3. Znajdź i usuń osieroconych
    deleted_count = 0
    logger.info(f"Rozpoczynam {'SYMULACJĘ' if dry_run else 'USUWANIE'} pustych deweloperów...")

    for slug, info in all_devs.items():
        if slug not in active_dev_slugs and not info["is_merged"]:
            portal_str = f" [{', '.join(info['portals'])}]" if info['portals'] else ""
            logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Usuwam dewelopera: {info['name']} ({slug}){portal_str}")
            if not dry_run:
                try:
                    shutil.rmtree(info["path"])
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Błąd podczas usuwania {slug}: {e}")
            else:
                deleted_count += 1

    logger.info(f"\nZakończono. {'Zasymulowano usunięcie' if dry_run else 'Usunięto'} {deleted_count} deweloperów.")
    if dry_run and deleted_count > 0:
        logger.info("Uruchom skrypt z parametrem --commit, aby faktycznie usunąć pliki.")

if __name__ == "__main__":
    import sys
    do_commit = "--commit" in sys.argv
    purge_empty_developers(dry_run=not do_commit)
