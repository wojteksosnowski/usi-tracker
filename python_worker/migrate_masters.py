"""
migrate_masters.py
==================
Migruje pliki master inwestycji do właściwego katalogu i formatu.

Reguły:
  - Wszystkie pliki master MUSZĄ siedzieć w Public/USImaster/
  - Nazwa pliku: inv_master_{IM-XXXX}.json
  - Format: { "master_id": "IM-XXXX", "members": [{"usi_inv_id": "INV-XXXXX"}, ...] }
  - ID-only: BRAK slugów, brak primary_id, brak secondary_id

Uruchomienie:
  ./venv/bin/python -m python_worker.migrate_masters [--dry-run] [--apply]
"""

import json
import os
import sys
import tempfile
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("migrate_masters")


def atomic_write(path: Path, data: dict):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def to_id_only_members(raw_members: list) -> list:
    """Konwertuje listę members do płaskiej struktury ID-only."""
    seen = set()
    result = []
    for m in raw_members:
        uid = m.get("usi_inv_id")
        if uid and uid not in seen:
            seen.add(uid)
            result.append({"usi_inv_id": uid})
    return result


def run(dry_run: bool = True):
    from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
    dropbox = Path(PUBLIC_USI_DIR).parent.parent   # DROPBOX_PATH
    usi_data = Path(USI_DATA_DIR)
    usi_master = dropbox / "Public" / "USImaster"
    usi_master.mkdir(parents=True, exist_ok=True)

    log.info(f"USIdata:   {usi_data}")
    log.info(f"USImaster: {usi_master}")
    log.info(f"Dry-run:   {dry_run}")

    migrated = []
    already_ok = []
    errors = []

    # ── 1. Stare pliki inv_master_*.json w USIdata/ ────────────────────────
    stray = list(usi_data.rglob("inv_master_*.json"))
    log.info(f"\nZnaleziono {len(stray)} błędnie umieszczonych plików inv_master_* w USIdata/")

    for src in stray:
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except Exception as e:
            log.error(f"  Nie można odczytać {src}: {e}")
            errors.append(str(src))
            continue

        master_id = data.get("master_id")
        if not master_id:
            log.warning(f"  Brak master_id w {src} — pomijam")
            errors.append(str(src))
            continue

        # Konwersja formatu
        raw_members = data.get("members", [])
        clean_members = to_id_only_members(raw_members)

        canonical = {
            "master_id": master_id,
            "members": clean_members,
        }

        dst = usi_master / f"inv_master_{master_id}.json"
        log.info(f"  MIGRATE  {src.relative_to(usi_data)} → USImaster/inv_master_{master_id}.json")
        log.info(f"           members: {[m['usi_inv_id'] for m in clean_members]}")

        if not dry_run:
            atomic_write(dst, canonical)
            src.unlink()
            log.info(f"           ✓ przeniesiono, stary plik usunięto")
        migrated.append(master_id)

    # ── 2. Stare usi_IM-*.json w USImaster/ (błędny format z merged_from) ─
    old_style = list(usi_master.glob("usi_IM-*.json"))
    log.info(f"\nZnaleziono {len(old_style)} starych plików usi_IM-*.json w USImaster/ do konwersji")

    for src in old_style:
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except Exception as e:
            log.error(f"  Nie można odczytać {src}: {e}")
            errors.append(str(src))
            continue

        master_id = (
            data.get("master_id")
            or data.get("usi_inv_id")
            or src.stem.replace("usi_", "")
        )
        if not master_id or not master_id.startswith("IM-"):
            log.warning(f"  Nieznany master_id w {src.name} — pomijam")
            errors.append(str(src))
            continue

        # Zbuduj members z merged_from (stary format)
        raw_merged = data.get("merged_from", [])
        clean_members = to_id_only_members(raw_merged)

        if not clean_members:
            log.warning(f"  {src.name} — brak members/merged_from, pomijam")
            errors.append(str(src))
            continue

        canonical = {
            "master_id": master_id,
            "members": clean_members,
        }

        dst = usi_master / f"inv_master_{master_id}.json"
        log.info(f"  CONVERT  {src.name} → inv_master_{master_id}.json")
        log.info(f"           members: {[m['usi_inv_id'] for m in clean_members]}")

        if not dry_run:
            atomic_write(dst, canonical)
            src.unlink()
            log.info(f"           ✓ skonwertowano, stary plik usunięto")
        migrated.append(master_id)

    # ── 3. Weryfikacja istniejących inv_master_*.json w USImaster/ ─────────
    good = list(usi_master.glob("inv_master_*.json"))
    log.info(f"\nSprawdzam {len(good)} plików inv_master_*.json w USImaster/ po migracji (dry={dry_run})")

    for f in good:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            log.error(f"  CORRUPTED: {f.name}: {e}")
            errors.append(str(f))
            continue

        members = d.get("members", [])
        bad_keys = [k for m in members for k in m if k != "usi_inv_id"]
        if bad_keys or not members:
            log.warning(f"  DIRTY: {f.name} — {len(members)} members, bad_keys={bad_keys}")
        else:
            log.info(f"  OK:    {f.name} — {[m['usi_inv_id'] for m in members]}")
            already_ok.append(f.name)

    log.info(f"\n{'='*60}")
    log.info(f"Podsumowanie{'  [DRY RUN]' if dry_run else ''}:")
    log.info(f"  Migrowanych / skonwertowanych: {len(migrated)}")
    log.info(f"  Już poprawnych:                {len(already_ok)}")
    log.info(f"  Błędów:                        {len(errors)}")
    if dry_run:
        log.info("\nAby zastosować zmiany, uruchom z flagą --apply")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", default=False)
    args = parser.parse_args()
    dry = not args.apply
    run(dry_run=dry)
