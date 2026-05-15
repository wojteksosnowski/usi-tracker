import csv
import json
import logging
import re
from pathlib import Path
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_manager import DeveloperManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock raw helpers
# ---------------------------------------------------------------------------

def _write_mock_rp(dev_dir: Path, slug: str, rp_id: str, rp_slug: str) -> None:
    """Write raw_rp_{slug}.json mock (skipped if a real raw already exists)."""
    path = dev_dir / f"raw_rp_{slug}.json"
    if path.exists() and not json.loads(path.read_text(encoding="utf-8")).get("_mock"):
        return  # real file — do not overwrite
    dev_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"id": rp_id, "slug": rp_slug, "_mock": True}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_or_merge_mock_oto(dev_dir: Path, slug: str, oto_id: str) -> bool:
    """Add oto_id to raw_oto_{slug}.json mock; create if missing. Returns True if changed."""
    path = dev_dir / f"raw_oto_{slug}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not existing.get("_mock"):
            return False  # real file — do not touch
        ids = existing.get("agency_ids") or (
            [existing["agency_id"]] if existing.get("agency_id") else []
        )
        if oto_id in ids:
            return False
        ids.append(oto_id)
        existing["agency_ids"] = ids
        existing["agency_id"] = ids[0]
        path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    dev_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"agency_id": oto_id, "agency_ids": [oto_id], "_mock": True},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return True


def _extract_name_from_raw(dev_dir: Path, slug: str) -> str:
    """Extract developer name from available raw files; fall back to slug."""
    for prefix in ("raw_rp_", "raw_oto_", "raw_to_"):
        candidate = dev_dir / f"{prefix}{slug}.json"
        if candidate.exists():
            try:
                raw = json.loads(candidate.read_text(encoding="utf-8"))
                n = raw.get("name")
                if n:
                    return n
            except Exception:
                continue
    return slug  # last resort


def _build_dev_from_raws(dev_dir: Path, slug: str, name: str | None, dm: DeveloperManager) -> None:
    """Rebuild usi_dev_{slug}.json portal_mapping from raw portal files in USIdev/{slug}/."""
    if not name:
        name = _extract_name_from_raw(dev_dir, slug)

    pm: dict = {"rp": None, "oto": None, "to": None}

    rp_file = dev_dir / f"raw_rp_{slug}.json"
    if rp_file.exists():
        raw = json.loads(rp_file.read_text(encoding="utf-8"))
        if raw.get("_mock"):
            pm["rp"] = {"id": raw.get("id", ""), "slug": raw.get("slug", "")}
        else:
            # Real RP dev profile — extract key fields
            pm["rp"] = {"id": str(raw.get("id", "")), "slug": raw.get("slug", "")}

    oto_file = dev_dir / f"raw_oto_{slug}.json"
    if oto_file.exists():
        raw = json.loads(oto_file.read_text(encoding="utf-8"))
        if raw.get("_mock"):
            pm["oto"] = {
                "agency_id": raw.get("agency_id"),
                "agency_ids": raw.get("agency_ids", []),
            }
        else:
            # Real OTO dev profile — try multiple known locations for agency id
            aid = (raw.get("agency_id")
                   or raw.get("id")
                   or (raw.get("owner") or {}).get("id")
                   or (raw.get("filterAttributes") or {}).get("sellerId")
                   or (raw.get("agency") or {}).get("id"))
            if aid:
                pm["oto"] = {"agency_id": str(aid), "agency_ids": [str(aid)]}

    to_file = dev_dir / f"raw_to_{slug}.json"
    if to_file.exists():
        raw = json.loads(to_file.read_text(encoding="utf-8"))
        aid = raw.get("agency_id") or raw.get("id")
        if aid:
            pm["to"] = {"agency_id": str(aid)}

    dm.create_developer_file({"developer_slug": slug, "name": name, "portal_mapping": pm})


def rebuild_devs_from_raws(
    dev_dir: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Build usi_dev_*.json for every USIdev subdirectory that contains raw files.

    Skips directories that already have usi_dev_*.json unless force=True.
    Returns (built, skipped).
    """
    target_dir = dev_dir or USI_DEV_DIR
    dm = DeveloperManager(USI_DATA_DIR, target_dir)
    built = skipped = 0

    for sub in sorted(target_dir.iterdir()):
        if not sub.is_dir():
            continue
        slug = sub.name
        has_raws = any(sub.glob("raw_*.json"))
        if not has_raws:
            skipped += 1
            continue
        dev_file = sub / f"usi_dev_{slug}.json"
        if dev_file.exists() and not force:
            skipped += 1
            continue
        if dry_run:
            logger.info(f"[dry-run] would build: {slug}")
            built += 1
            continue
        try:
            _build_dev_from_raws(sub, slug, None, dm)
            built += 1
            logger.info(f"Built: {slug}")
        except Exception as e:
            logger.error(f"Failed to build {slug}: {e}")
            skipped += 1

    return built, skipped


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
                _write_mock_rp(target_dir / slug, slug, rid, rslug)
                touched_slugs.add(slug)

            for slug, oid in slugs_oto:
                _write_or_merge_mock_oto(target_dir / slug, slug, oid)
                touched_slugs.add(slug)

            for slug in touched_slugs:
                _build_dev_from_raws(target_dir / slug, slug, dev_name, dm)
                created += 1
                logger.info(f"Built developer: {slug}")

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
