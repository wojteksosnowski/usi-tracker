"""
migrate_dev_files.py — Migracja plików deweloperów do trójpoziomowej architektury.

Co robi:
  1. Przemianowuje usi_dev_{slug}.json → usi_dev_{usi_dev_id}_{slug}.json
  2. Wyciąga events[] z Level 2 → dev_log_{slug}.txt (JSONL, append)
  3. Wyciąga merged_from[] z Level 2 → dev_master_{DM-NNNNN}.json (Level 3)
  4. Ustawia master_id w Level 2 rodzica i każdego dziecka
  5. Usuwa events[] i merged_from[] z Level 2

Uruchomienie (dry-run, domyślne):
    python3 -m python_worker.migrate_dev_files

Zastosowanie zmian:
    python3 -m python_worker.migrate_dev_files --apply
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_manager import DeveloperManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _load_all_devs(dev_dir: Path) -> list[tuple[Path, dict]]:
    """Returns [(file_path, dev_data)] for every usi_dev_*.json found."""
    seen_slugs: set[str] = set()
    results = []

    for pattern in ("*/usi_dev_*.json", "usi_dev_*.json"):
        for f in sorted(dev_dir.glob(pattern)):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Pominięto {f}: {e}")
                continue
            slug = d.get("developer_slug")
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            results.append((f, d))

    return results


def _needs_rename(file_path: Path, dev_data: dict) -> tuple[bool, Path]:
    """Returns (needs_rename, target_path)."""
    dev_id = dev_data.get("usi_dev_id", "")
    slug = dev_data.get("developer_slug", "")
    expected_name = f"usi_dev_{dev_id}_{slug}.json"
    if file_path.name == expected_name:
        return False, file_path
    target = file_path.parent / expected_name
    # Ensure it's in the canonical subdir (USIdev/{slug}/)
    canonical_subdir = file_path.parent.parent / slug
    target = canonical_subdir / expected_name
    return True, target


def migrate(dev_dir: Path, apply: bool) -> None:
    dm = DeveloperManager(USI_DATA_DIR, dev_dir)
    all_devs = _load_all_devs(dev_dir)

    print(f"\n=== {'ZASTOSOWANIE ZMIAN' if apply else 'DRY-RUN'} ===")
    print(f"Znaleziono {len(all_devs)} plików deweloperów.\n")

    # Pass 1: Collect master candidates (devs with merged_from[])
    # Build: usi_dev_id → dm_id mapping for devs becoming masters
    master_map: dict[str, str] = {}   # usi_dev_id → DM-NNNNN
    dm_counter = dm._get_next_counter.__func__  # reference to avoid confusion

    # We'll use DeveloperManager._get_next_counter directly
    def next_dm_id() -> str:
        n = dm._get_next_counter("dm")
        return f"DM-{n:04d}"

    rename_count = 0
    log_count = 0
    master_count = 0

    for file_path, dev_data in all_devs:
        dev_id = dev_data.get("usi_dev_id", "")
        slug = dev_data.get("developer_slug", "")
        merged_from = dev_data.get("merged_from", [])

        needs_rename, new_path = _needs_rename(file_path, dev_data)
        events = dev_data.get("events", [])
        has_master = bool(merged_from)

        print(f"  [{slug}] ({dev_id})")
        if needs_rename:
            print(f"    → Przemianuj: {file_path.name} → {new_path.name}")
            rename_count += 1
        if events:
            print(f"    → Logi: {len(events)} eventów → dev_log_{slug}.txt")
            log_count += 1
        if has_master:
            dm_id = next_dm_id() if apply else f"DM-XXXX"
            master_map[dev_id] = dm_id
            print(f"    → Master: dev_master_{dm_id}.json ({len(merged_from)} dzieci)")
            master_count += 1

    print(f"\nPodsumowanie:")
    print(f"  Przemianowania:    {rename_count}")
    print(f"  Pliki logów:       {log_count}")
    print(f"  Pliki dev_master:  {master_count}")

    if not apply:
        print("\nUruchom z --apply żeby zastosować zmiany.")
        return

    # Pass 2: Apply changes
    slug_to_dev_id: dict[str, str] = {d.get("developer_slug"): d.get("usi_dev_id") for _, d in all_devs}

    for file_path, dev_data in all_devs:
        slug = dev_data.get("developer_slug", "")
        dev_id = dev_data.get("usi_dev_id", "")
        merged_from = dev_data.get("merged_from", [])
        events = dev_data.get("events", [])

        canonical_subdir = dev_dir / slug
        canonical_subdir.mkdir(parents=True, exist_ok=True)

        # Write events to log file
        if events:
            log_path = canonical_subdir / f"dev_log_{slug}.txt"
            with open(log_path, "a", encoding="utf-8") as lf:
                for ev in reversed(events):  # oldest first in log
                    if "at" not in ev:
                        ev = {"at": datetime.now().isoformat(), **ev}
                    lf.write(json.dumps(ev, ensure_ascii=False) + "\n")
            logger.info(f"Wrote {len(events)} log entries for {slug}")

        # Create dev_master file if this dev has merged children
        if merged_from and dev_id in master_map:
            dm_id = master_map[dev_id]
            master_data = {
                "dev_master_id": dm_id,
                "master_usi_dev_id": dev_id,
                "master_slug": slug,
                "merged_from": merged_from,
                "dismissed": [],
            }
            master_path = canonical_subdir / f"dev_master_{dm_id}.json"
            master_path.write_text(json.dumps(master_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"Created {master_path}")
            dev_data["master_id"] = dm_id

        # Strip Level 3 fields from Level 2
        dev_data.pop("events", None)
        dev_data.pop("merged_from", None)

        # Rename / save Level 2 file
        new_filename = f"usi_dev_{dev_id}_{slug}.json"
        new_path = canonical_subdir / new_filename
        new_path.write_text(json.dumps(dev_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Remove old file if at different path
        if file_path != new_path and file_path.exists():
            file_path.unlink()
            logger.info(f"Removed old file {file_path}")

    # Pass 3: Set master_id on child devs (those with parent_id)
    # Reload all devs to get up-to-date paths
    all_devs_updated = _load_all_devs(dev_dir)
    # Build parent_id → dm_id from master_map using usi_dev_id
    for _, dev_data in all_devs_updated:
        parent_id = dev_data.get("parent_id")
        if not parent_id:
            continue
        dm_id = master_map.get(parent_id)
        if not dm_id:
            continue
        if dev_data.get("master_id") != dm_id:
            dev_data["master_id"] = dm_id
            slug = dev_data.get("developer_slug", "")
            dev_id = dev_data.get("usi_dev_id", "")
            new_path = dev_dir / slug / f"usi_dev_{dev_id}_{slug}.json"
            new_path.write_text(json.dumps(dev_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"Set master_id={dm_id} on child {slug}")

    print(f"\nMigracja zakończona. Sprawdź logi powyżej.")


def main():
    parser = argparse.ArgumentParser(description="Migracja plików deweloperów do trójpoziomowej architektury")
    parser.add_argument("--apply", action="store_true", help="Zastosuj zmiany (domyślnie: dry-run)")
    args = parser.parse_args()

    migrate(Path(USI_DEV_DIR), apply=args.apply)


if __name__ == "__main__":
    main()
