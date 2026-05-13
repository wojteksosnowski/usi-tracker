import csv
import json
import logging
import re
from pathlib import Path
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_manager import DeveloperManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def init_developers_from_konkurenci(
    konkurenci_path: Path | None = None,
    dev_dir: Path | None = None,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Initialize developers from Konkurenci.csv with split logic for dual records.
    
    If a row has both RP and OTO identifiers, it creates two separate developer profiles.
    """
    csv_path = konkurenci_path or (Path(__file__).parent.parent / "reference-data" / "coda" / "Konkurenci.csv")
    target_dir = dev_dir or USI_DEV_DIR
    dm = DeveloperManager(USI_DATA_DIR, target_dir)

    created = 0
    skipped = 0

    if not csv_path.exists():
        logger.error(f"Konkurenci.csv not found: {csv_path}")
        return 0, 0

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dev_name = row.get("Deweloper", "").strip()
            dev_slug = row.get("usiFolder", "").strip()
            rp_id = row.get("rpID", "").strip()
            rp_slug = row.get("rpSlug", "").strip()
            oto_raw = row.get("otoID", "").strip()

            if not dev_slug or not dev_name:
                continue

            has_rp = bool(rp_id or rp_slug)
            has_oto = bool(oto_raw)

            if has_rp or has_oto:
                dev_data = {
                    "developer_slug": dev_slug,
                    "name": dev_name,
                    "portal_mapping": {
                        "rp": {"id": rp_id, "slug": rp_slug} if has_rp else None,
                        "oto": {"agency_id": re.sub(r"^ID", "", oto_raw)} if has_oto else None,
                        "to": None
                    }
                }
                
                if not dry_run:
                    dm.create_developer_file(dev_data)
                created += 1
                logger.info(f"Created developer: {dev_slug} (RP: {has_rp}, OTO: {has_oto})")
            else:
                skipped += 1

    return created, skipped


def migrate_developers():
    """
    Scans USI_DATA_DIR for unique developers and creates metadata files in USI_DEV_DIR.
    """
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    
    unique_devs = {} # slug -> name
    
    logger.info(f"Scanning {USI_DATA_DIR} for investments...")
    
    investment_files = list(USI_DATA_DIR.rglob("usi_*.json"))
    logger.info(f"Found {len(investment_files)} investment files.")
    
    for inv_file in investment_files:
        # Skip existing dev files if they were in the wrong place
        if inv_file.name.startswith("usi_dev_"):
            continue
            
        try:
            with open(inv_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            dev_slug = data.get("developer_slug")
            dev_name = data.get("developer")
            
            if dev_slug and dev_name:
                if dev_slug not in unique_devs:
                    unique_devs[dev_slug] = dev_name
                elif unique_devs[dev_slug] != dev_name:
                    # In case of name mismatch for same slug, we can log it but we keep the first one
                    # logger.warning(f"Name mismatch for {dev_slug}: '{unique_devs[dev_slug]}' vs '{dev_name}'")
                    pass
        except Exception as e:
            logger.error(f"Error reading {inv_file}: {e}")
            
    logger.info(f"Extracted {len(unique_devs)} unique developers.")
    
    created_count = 0
    updated_count = 0
    
    for dev_slug, dev_name in unique_devs.items():
        dev_file = USI_DEV_DIR / f"usi_dev_{dev_slug}.json"
        
        if dev_file.exists():
            # If exists, we might want to update the name if it's missing or something
            # but for now let's just count it
            updated_count += 1
            # We still call create_developer_file to update updated_at audit
        else:
            created_count += 1
            
        existing_pm = None
        if dev_file.exists():
            try:
                existing_pm = json.loads(dev_file.read_text(encoding="utf-8")).get("portal_mapping")
            except Exception:
                pass

        dev_data = {
            "developer_slug": dev_slug,
            "name": dev_name,
            "portal_mapping": existing_pm or {"rp": None, "oto": None, "to": None},
        }
        dm.create_developer_file(dev_data)

    logger.info(f"Migration complete: {created_count} new, {updated_count} updated.")


def backfill_from_konkurenci(
    konkurenci_path: Path | None = None,
    dev_dir: Path | None = None,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Populate portal_mapping.rp / .oto from Konkurenci.csv for existing dev files.

    Konkurenci.csv columns used: usiFolder, rpID, rpSlug, otoID.
    Only fills in data that is currently missing (null) — never overwrites.
    Returns (updated, skipped) counts.
    """
    csv_path = konkurenci_path or (Path(__file__).parent.parent / "reference-data" / "coda" / "Konkurenci.csv")
    target_dir = dev_dir or USI_DEV_DIR

    updated = 0
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dev_slug = row.get("usiFolder", "").strip()
            rp_id = row.get("rpID", "").strip()
            rp_slug = row.get("rpSlug", "").strip()
            oto_raw = row.get("otoID", "").strip()

            if not dev_slug:
                continue

            dev_file = target_dir / f"usi_dev_{dev_slug}.json"
            if not dev_file.exists():
                logger.debug("backfill: no file for %s — skipping", dev_slug)
                skipped += 1
                continue

            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("backfill: could not read %s: %s", dev_file.name, e)
                skipped += 1
                continue

            pm = data.get("portal_mapping") or {}
            changed = False

            if not pm.get("rp") and (rp_id or rp_slug):
                pm["rp"] = {"id": rp_id, "slug": rp_slug}
                changed = True

            # otoID in CSV has format "ID8495786" — strip the "ID" prefix
            oto_id_numeric = re.sub(r"^ID", "", oto_raw) if oto_raw else ""
            if not pm.get("oto") and oto_id_numeric:
                pm["oto"] = {"agency_id": oto_id_numeric}
                changed = True

            if not changed:
                skipped += 1
                continue

            data["portal_mapping"] = pm
            if not dry_run:
                dm = DeveloperManager(USI_DATA_DIR, target_dir)
                dm.create_developer_file(data)
            logger.info("backfill: %s → rp=%s oto=%s%s", dev_slug, pm.get("rp"), pm.get("oto"), " [dry]" if dry_run else "")
            updated += 1

    logger.info("backfill_from_konkurenci: %d updated, %d skipped%s", updated, skipped, " (dry run)" if dry_run else "")
    return updated, skipped


if __name__ == "__main__":
    migrate_developers()
