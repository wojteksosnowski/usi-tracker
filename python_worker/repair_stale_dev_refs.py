"""
repair_stale_dev_refs.py — Naprawia wiszące referencje do DEV IDs usuniętych przez split.

Po podziale multi-portal usi_dev_*.json na pliki per-portal stare DEV IDs zostały usunięte,
ale referencje w dev_master.master_usi_dev_id, parent_id, suggestions[] i dismissed[]
nadal wskazują na nieistniejące pliki.

Mapping stary→nowy odtwarzany jest z dev_master.merged_from.

Dry-run (domyślny):
    python3 -m python_worker.repair_stale_dev_refs

Zastosowanie zmian:
    python3 -m python_worker.repair_stale_dev_refs --apply
"""

import argparse
import json
import logging
import re
from pathlib import Path

from python_worker.config import USI_DEV_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEV_RE = re.compile(r"DEV-\d+")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_existing_ids(dev_root: Path) -> set[str]:
    ids = set()
    for f in dev_root.glob("*/usi_dev_*.json"):
        try:
            d = _load(f)
            if d.get("usi_dev_id"):
                ids.add(d["usi_dev_id"])
        except Exception:
            pass
    return ids


def _build_stale_mapping(dev_root: Path, existing_ids: set[str]) -> dict[str, str]:
    """Returns {stale_id: primary_new_id} reconstructed from dev_master.merged_from."""
    mapping: dict[str, str] = {}
    for master_file in dev_root.glob("*/dev_master_*.json"):
        try:
            master = _load(master_file)
        except Exception:
            continue
        stale_id = master.get("master_usi_dev_id")
        if not stale_id or stale_id in existing_ids:
            continue
        new_ids = [e["usi_dev_id"] for e in master.get("merged_from", []) if e.get("usi_dev_id")]
        if new_ids:
            mapping[stale_id] = new_ids[0]
    return mapping


def repair(dev_root: Path, apply: bool) -> None:
    existing_ids = _build_existing_ids(dev_root)
    stale_map = _build_stale_mapping(dev_root, existing_ids)

    if not stale_map:
        print("Brak stale DEV IDs do naprawy.")
        return

    print(f"Znalezione stale mappings: {len(stale_map)}")
    for old, new in sorted(stale_map.items()):
        print(f"  {old} → {new}")

    master_fixes = 0
    dev_fixes = 0

    # --- Fix dev_master files ---
    for master_file in sorted(dev_root.glob("*/dev_master_*.json")):
        try:
            master = _load(master_file)
        except Exception as e:
            logger.warning(f"Pominięto {master_file}: {e}")
            continue

        changed = False

        # master_usi_dev_id
        mid = master.get("master_usi_dev_id")
        if mid and mid in stale_map:
            print(f"  [master] {master_file.name}: master_usi_dev_id {mid} → {stale_map[mid]}")
            if apply:
                master["master_usi_dev_id"] = stale_map[mid]
            changed = True

        # dismissed[].usi_dev_id
        for entry in master.get("dismissed", []):
            did = entry.get("usi_dev_id")
            if did and did in stale_map:
                print(f"  [master] {master_file.name}: dismissed.usi_dev_id {did} → {stale_map[did]}")
                if apply:
                    entry["usi_dev_id"] = stale_map[did]
                changed = True

        # merged_from[].usi_dev_id (shouldn't happen but check)
        for entry in master.get("merged_from", []):
            mid2 = entry.get("usi_dev_id")
            if mid2 and mid2 in stale_map:
                print(f"  [master] {master_file.name}: merged_from.usi_dev_id {mid2} → {stale_map[mid2]}")
                if apply:
                    entry["usi_dev_id"] = stale_map[mid2]
                changed = True

        if changed:
            master_fixes += 1
            if apply:
                _save(master_file, master)

    # --- Fix usi_dev files ---
    for dev_file in sorted(dev_root.glob("*/usi_dev_*.json")):
        try:
            dev = _load(dev_file)
        except Exception as e:
            logger.warning(f"Pominięto {dev_file}: {e}")
            continue

        changed = False

        # parent_id
        pid = dev.get("parent_id")
        if pid and pid in stale_map:
            print(f"  [dev] {dev_file.name}: parent_id {pid} → {stale_map[pid]}")
            if apply:
                dev["parent_id"] = stale_map[pid]
            changed = True

        # master_id (unlikely but check)
        amid = dev.get("master_id")
        if amid and amid in stale_map:
            print(f"  [dev] {dev_file.name}: master_id {amid} → {stale_map[amid]}")
            if apply:
                dev["master_id"] = stale_map[amid]
            changed = True

        # suggestions[].usi_dev_id
        suggestions = dev.get("suggestions") or []
        new_suggestions = []
        for s in suggestions:
            sid = s.get("usi_dev_id") or s.get("id")
            if sid and sid in stale_map:
                print(f"  [dev] {dev_file.name}: suggestion {sid} → {stale_map[sid]}")
                if apply:
                    if s.get("usi_dev_id"):
                        s["usi_dev_id"] = stale_map[sid]
                    if s.get("id"):
                        s["id"] = stale_map[sid]
                new_suggestions.append(s)
                changed = True
            elif sid and sid not in existing_ids:
                print(f"  [dev] {dev_file.name}: suggestion {sid} — brak pliku, usuwam")
                changed = True
                # don't append — drop it
            else:
                new_suggestions.append(s)

        if apply and changed and "suggestions" in dev:
            dev["suggestions"] = new_suggestions

        if changed:
            dev_fixes += 1
            if apply:
                _save(dev_file, dev)

    mode = "ZASTOSOWANIE ZMIAN" if apply else "DRY-RUN"
    print(f"\n=== {mode} ===")
    print(f"dev_master do naprawy: {master_fixes}")
    print(f"usi_dev do naprawy: {dev_fixes}")
    if not apply:
        print("Uruchom z --apply żeby zastosować zmiany.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    repair(Path(USI_DEV_DIR), apply=args.apply)


if __name__ == "__main__":
    main()
