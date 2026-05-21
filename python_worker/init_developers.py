import csv
import json
import logging
import re
from pathlib import Path
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_manager import DeveloperManager
from python_worker.adapters import PORTAL_MAPPING
from usi_scrapers import resolve_path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Removed unused mock functions


# ---------------------------------------------------------------------------
# Main importer
# ---------------------------------------------------------------------------

def init_developers_from_konkurenci(
    konkurenci_path: Path | None = None,
    dev_dir: Path | None = None,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Initialize/update developers from Konkurenci.csv using mock raw JSONs.

    Rules:
    - Each RP ID → its own developer record (RP IDs are authoritative per-firm).
    - OTO agency_ids may be combined in one record but never together with an RP ID.
    - Row with both rpID and otoID → split:
        * RP-only record  (slug = usiFolder)
        * OTO-only record (slug = otoSlug if distinct, else warn and keep merged)
    - Same usiFolder in multiple rows → OTO agency_ids accumulated in mock raw.
    - Real raw files (no _mock flag) are never overwritten.
    """
    csv_path = konkurenci_path or (
        Path(__file__).parent.parent / "reference-data" / "coda" / "Konkurenci.csv"
    )
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
            rp_id    = row.get("rpID", "").strip()
            rp_slug  = row.get("rpSlug", "").strip()
            oto_raw  = row.get("otoID", "").strip()
            oto_slug = row.get("otoSlug", "").strip()

            if not dev_slug or not dev_name:
                continue

            has_rp  = bool(rp_id or rp_slug)
            has_oto = bool(oto_raw)

            if not has_rp and not has_oto:
                skipped += 1
                continue

            oto_id = re.sub(r"^ID", "", oto_raw) if has_oto else None

            # Determine which slugs get which raw files
            # records: list of (slug, write_rp, rp_id, rp_slug, write_oto, oto_id)
            if has_rp and has_oto:
                if oto_slug and oto_slug != dev_slug:
                    # Clean split: two separate records
                    slugs_rp  = [(dev_slug, rp_id, rp_slug)]
                    slugs_oto = [(oto_slug, oto_id)]
                else:
                    logger.warning(
                        f"[split] brak otoSlug dla '{dev_name}' (usiFolder={dev_slug})"
                        " — RP+OTO w jednym rekordzie"
                    )
                    slugs_rp  = [(dev_slug, rp_id, rp_slug)]
                    slugs_oto = [(dev_slug, oto_id)]
            elif has_rp:
                slugs_rp  = [(dev_slug, rp_id, rp_slug)]
                slugs_oto = []
            else:
                slugs_rp  = []
                slugs_oto = [(dev_slug, oto_id)]

            if dry_run:
                created += len({s for s, *_ in slugs_rp} | {s for s, *_ in slugs_oto})
                continue

            touched_slugs: set[str] = set()

            for slug, rid, rslug in slugs_rp:
                dev_data = dm.get_developer(slug)
                if not dev_data:
                    dev_data = {"developer_slug": slug, "name": dev_name, "portal_mapping": {"rp": None, "oto": None, "to": None}}
                if rid:
                    dev_data["portal_mapping"]["rp"] = {"id": rid, "slug": rslug}
                dm.create_developer_file(dev_data)
                touched_slugs.add(slug)

            for slug, oid in slugs_oto:
                dev_data = dm.get_developer(slug)
                if not dev_data:
                    dev_data = {"developer_slug": slug, "name": dev_name, "portal_mapping": {"rp": None, "oto": None, "to": None}}
                if oid:
                    if not dev_data["portal_mapping"].get("oto"):
                        dev_data["portal_mapping"]["oto"] = {"agency_id": oid, "agency_ids": []}
                    if oid not in dev_data["portal_mapping"]["oto"]["agency_ids"]:
                        dev_data["portal_mapping"]["oto"]["agency_ids"].append(oid)
                dm.create_developer_file(dev_data)
                touched_slugs.add(slug)

            for slug in touched_slugs:
                created += 1
                logger.info(f"Built/Updated developer: {slug}")

    return created, skipped


# ---------------------------------------------------------------------------
# Legacy helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------

def migrate_developers():
    """Scans USI_DATA_DIR for unique developers and creates metadata files in USI_DEV_DIR."""
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    unique_devs = {}

    logger.info(f"Scanning {USI_DATA_DIR} for investments...")
    investment_files = list(USI_DATA_DIR.rglob("usi_*.json"))
    logger.info(f"Found {len(investment_files)} investment files.")

    for inv_file in investment_files:
        if inv_file.name.startswith("usi_dev_"):
            continue
        try:
            with open(inv_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            dev_slug = data.get("developer_slug")
            dev_name = data.get("developer")
            if dev_slug and dev_name and dev_slug not in unique_devs:
                unique_devs[dev_slug] = dev_name
        except Exception as e:
            logger.error(f"Error reading {inv_file}: {e}")

    logger.info(f"Extracted {len(unique_devs)} unique developers.")
    created_count = 0
    updated_count = 0

    for dev_slug, dev_name in unique_devs.items():
        dev_file = USI_DEV_DIR / dev_slug / f"usi_dev_{dev_slug}.json"
        if dev_file.exists():
            updated_count += 1
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


if __name__ == "__main__":
    migrate_developers()
