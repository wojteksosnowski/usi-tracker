"""
unmerge_to_stubs.py — usuwa błędne scalenia deweloperów TO-stub.

TO-stub: deweloper z wyłącznie wpisem TabelaOfert (portal_mapping.to, bez rp i oto),
bez agency_id — powstały jako "placeholder" przed auto-merge i nie powinny być
scalane z prawdziwymi deweloperami.

Uruchomienie (dry-run, domyślne):
    python3 -m python_worker.unmerge_to_stubs

Zastosowanie zmian:
    python3 -m python_worker.unmerge_to_stubs --apply
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


def _is_to_stub(dev: dict) -> bool:
    pm = dev.get("portal_mapping") or {}
    to_entry = pm.get("to")
    if not to_entry:
        return False
    if pm.get("rp") or pm.get("oto"):
        return False
    if to_entry.get("agency_id"):
        return False
    return bool(to_entry.get("slug"))


def find_to_stub_merges(dev_dir: Path) -> list[tuple[dict, dict]]:
    """Returns list of (parent_dev, child_dev) pairs where child is a TO-stub."""
    # Build child_id → master_usi_dev_id from dev_master files
    child_to_master: dict[str, str] = {}
    for master_file in dev_dir.glob("*/dev_master_*.json"):
        try:
            m = json.loads(master_file.read_text(encoding="utf-8"))
            master_dev_id = m.get("master_usi_dev_id")
            for entry in m.get("merged_from", []):
                cid = entry.get("usi_dev_id")
                if cid and master_dev_id:
                    child_to_master[cid] = master_dev_id
        except Exception as e:
            logger.warning(f"Pominięto {master_file}: {e}")

    all_devs: dict[str, dict] = {}
    for f in dev_dir.glob("*/usi_dev_*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            dev_id = d.get("usi_dev_id")
            if dev_id:
                all_devs[dev_id] = d
        except Exception as e:
            logger.warning(f"Pominięto {f}: {e}")

    pairs = []
    for dev_id, child in all_devs.items():
        parent_dev_id = child_to_master.get(dev_id)
        if not parent_dev_id:
            continue
        if not _is_to_stub(child):
            continue
        parent = all_devs.get(parent_dev_id)
        if not parent:
            logger.warning(f"Nie znaleziono parenta {parent_dev_id} dla {dev_id}")
            continue
        pairs.append((parent, child))

    return pairs


def unmerge_to_stub_pair(dm: DeveloperManager, parent: dict, child: dict, apply: bool) -> bool:
    parent_slug = parent["developer_slug"]
    child_slug = child["developer_slug"]
    child_to_slug = (child.get("portal_mapping") or {}).get("to", {}).get("slug", "")
    parent_to = (parent.get("portal_mapping") or {}).get("to")
    parent_to_slug = (parent_to or {}).get("slug", "") if isinstance(parent_to, dict) else ""

    print(f"  {parent_slug} ← {child_slug}  (TO slug: {child_to_slug})")

    to_mapping_cleanup = bool(parent_to_slug and parent_to_slug == child_to_slug)
    if to_mapping_cleanup:
        print(f"    ⚠ parent.portal_mapping.to = {{slug: {parent_to_slug}}} zostanie wyczyszczone")

    if not apply:
        return True

    ok = dm.unmerge_by_id(parent["usi_dev_id"], child["usi_dev_id"])
    if not ok:
        logger.error(f"  unmerge_by_id({parent['usi_dev_id']}, {child['usi_dev_id']}) zwrócił False")
        return False

    # Additional cleanup: clear portal_mapping.to on parent if it was the stub's slug
    if to_mapping_cleanup:
        fresh_parent = dm.get_developer_by_id(parent["usi_dev_id"])
        if fresh_parent:
            pm = fresh_parent.setdefault("portal_mapping", {})
            pm["to"] = None
            dm.create_developer_file(fresh_parent)
            logger.info(f"  Wyczyszczono portal_mapping.to na {parent_slug}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Usuń błędne scalenia TO-stub deweloperów")
    parser.add_argument("--apply", action="store_true", help="Zastosuj zmiany (domyślnie: dry-run)")
    args = parser.parse_args()

    dev_dir = Path(USI_DEV_DIR)
    dm = DeveloperManager(USI_DATA_DIR, dev_dir)

    pairs = find_to_stub_merges(dev_dir)

    if not pairs:
        print("Nie znaleziono żadnych błędnych scaleń TO-stub.")
        return

    mode = "ZASTOSOWANIE ZMIAN" if args.apply else "DRY-RUN (bez zmian)"
    print(f"\n=== {mode} ===")
    print(f"Znaleziono {len(pairs)} par do rozłączenia:\n")

    ok_count = 0
    for parent, child in sorted(pairs, key=lambda p: p[0]["developer_slug"]):
        ok = unmerge_to_stub_pair(dm, parent, child, apply=args.apply)
        if ok:
            ok_count += 1

    print(f"\nGotowe: {ok_count}/{len(pairs)} par {'rozłączono' if args.apply else 'do rozłączenia'}.")
    if not args.apply:
        print("Uruchom z --apply żeby zastosować zmiany.")


if __name__ == "__main__":
    main()
