import csv
import json
import logging
import re
from pathlib import Path
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_manager import DeveloperManager
from usi_scrapers import api as scraper_api

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


def _build_dev_from_raws(dev_subdir: Path, dev_slug: str, dev_name: str, dm: DeveloperManager) -> bool:
    """Builds per-portal usi_dev_*.json files from whichever raw files exist in the subdir."""
    from usi_scrapers import api as scraper_api

    raw_files = list(dev_subdir.glob("raw_*.json"))
    if not raw_files:
        return False

    built = False
    for raw_file in raw_files:
        # Oczekiwany wzorzec nazwy pliku: raw_{portal}_{id}.json
        parts = raw_file.stem.split("_")
        if len(parts) < 3:
            continue
        portal = parts[1]
        if portal not in ("rp", "oto", "to"):
            continue

        try:
            raw_text = raw_file.read_text(encoding="utf-8")
            if not raw_text.strip():
                continue
            raw_data = json.loads(raw_text)
            
            # KRYTYCZNA POPRAWKA: Bezwzględna delegacja ekstrakcji do bazy mapowań usi-scrapers
            meta = scraper_api.extract_developer_meta(raw_data, portal)
            portal_id = meta.get("id")
            
            # Wymagamy obecności ID, nie zgadujemy z nazwy pliku
            if not portal_id:
                raise ValueError(f"Brak ID w surowych danych. Zgodnie z polityką ID-Only nie fallbackujemy do nazwy pliku.")
            
            # Budowa struktury portal_mapping dla pojedynczego pliku Level 2
            pm = {"rp": None, "oto": None, "to": None}
            
            if portal == "oto":
                pm["oto"] = {"agency_id": str(portal_id) if portal_id else None, "slug": dev_slug}
            else:
                pm[portal] = {"id": str(portal_id) if portal_id else None, "slug": dev_slug}
            
            # Ustalenie nazwy z zachowaniem hierarchii ważności źródeł
            name = dev_name or meta.get("name") or raw_data.get("name") or dev_slug
            
            dev_data = {
                "developer_slug": dev_slug,
                "name": name,
                "portal_mapping": pm
            }
            
            dm.create_developer_file(dev_data)
            built = True
        except Exception as e:
            logger.warning(f"Failed to build dev from {raw_file}: {e}")

    return built


def rebuild_devs_from_raws(dev_dir: Path | None = None, data_dir: Path | None = None) -> int:
    """Scans all USIdev subdirs and builds per-portal usi_dev_*.json from raw files."""
    target_dir = dev_dir or USI_DEV_DIR
    dm = DeveloperManager(data_dir or USI_DATA_DIR, target_dir)
    
    count = 0
    if not target_dir.exists():
        return 0
        
    for subdir in target_dir.iterdir():
        if not subdir.is_dir() or subdir.name.startswith("_") or subdir.name.startswith("."):
            continue
            
        # Try to find developer name from existing files
        dev_name = None
        for usi_file in subdir.glob("usi_dev_*.json"):
            try:
                dev_name = json.loads(usi_file.read_text(encoding="utf-8")).get("name")
                if dev_name: break
            except: pass
            
        if _build_dev_from_raws(subdir, subdir.name, dev_name, dm):
            count += 1
            
    logger.info(f"Rebuild from raws complete: {count} developers processed.")
    return count

