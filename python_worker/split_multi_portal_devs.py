"""
split_multi_portal_devs.py — Dzieli pliki usi_dev_*.json z wieloma portalami na pliki 1:1.

Reguła: każdy usi_dev_{id}_{slug}.json musi odpowiadać dokładnie jednemu raw_{portal}_{slug}.json.
Pliki z N portalami (N > 1) są dzielone na N osobnych plików, każdy z własnym DEV-ID.
Wspólny dev_master grupuje nowe rekordy.

Dry-run (domyślny):
    python3 -m python_worker.split_multi_portal_devs

Zastosowanie zmian:
    python3 -m python_worker.split_multi_portal_devs --apply
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

PORTALS = ("rp", "oto", "to")
_RELATIONAL_FIELDS = ("parent_id", "master_id", "merged_from", "events")


def _portals_present(pm: dict) -> list[str]:
    return [p for p in PORTALS if pm.get(p)]


def _split_dev(dev_file: Path, dev: dict, apply: bool, dm: DeveloperManager) -> list[str]:
    """Split one multi-portal dev file into per-portal files. Returns list of new DEV IDs."""
    slug = dev.get("developer_slug", dev_file.parent.name)
    pm = dev.get("portal_mapping") or {}
    portals = _portals_present(pm)

    print(f"  [{slug}] DEV={dev.get('usi_dev_id')} portals={portals}")

    if not apply:
        for p in portals:
            print(f"    → usi_dev_NEW_{slug}.json  ({p} only)")
        return []

    new_ids = []
    base = {k: v for k, v in dev.items() if k not in _RELATIONAL_FIELDS}

    for portal in portals:
        new_id = dm.generate_usi_id("DEV")
        pm_single: dict = {"rp": None, "oto": None, "to": None}
        pm_single[portal] = pm[portal]
        new_dev = {
            **base,
            "usi_dev_id": new_id,
            "portal_mapping": pm_single,
            "audit": {
                "created_at": dev.get("audit", {}).get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "split_from": dev.get("usi_dev_id"),
            },
        }
        dm.create_developer_file(new_dev)
        new_ids.append(new_id)
        logger.info(f"  Created {new_id} ({portal}) for {slug}")

    # Update or create dev_master grouping the new per-portal records
    existing_master_id = dev.get("master_id")
    master_file: Path | None = None
    master: dict | None = None

    if existing_master_id:
        candidates = list((dm.dev_dir / slug).glob(f"dev_master_{existing_master_id}.json"))
        if candidates:
            master_file = candidates[0]
            try:
                master = json.loads(master_file.read_text(encoding="utf-8"))
            except Exception:
                master = None

    if master is None:
        dm_id = dm.generate_usi_id("DM")
        master = {
            "dev_master_id": dm_id,
            "master_usi_dev_id": new_ids[0],
            "master_slug": slug,
            "merged_from": [],
            "dismissed": [],
        }
        master_file = dm.dev_dir / slug / f"dev_master_{dm_id}.json"

    existing_merged = {e["usi_dev_id"] for e in master.get("merged_from", []) if e.get("usi_dev_id")}
    for nid in new_ids:
        if nid not in existing_merged:
            master.setdefault("merged_from", []).append({"usi_dev_id": nid})

    master_file.parent.mkdir(parents=True, exist_ok=True)
    master_file.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")

    # Set master_id on each new per-portal file
    for nid in new_ids:
        candidates = list((dm.dev_dir / slug).glob(f"usi_dev_{nid}_{slug}.json"))
        if candidates:
            try:
                ndev = json.loads(candidates[0].read_text(encoding="utf-8"))
                ndev["master_id"] = master["dev_master_id"]
                candidates[0].write_text(json.dumps(ndev, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not set master_id on {candidates[0]}: {e}")

    # Remove original multi-portal file
    dev_file.unlink()
    logger.info(f"  Removed original {dev_file.name}")

    return new_ids


def split_multi_portal_devs(dev_dir: Path, apply: bool) -> None:
    dm = DeveloperManager(USI_DATA_DIR, dev_dir)
    affected = 0
    total_new = 0

    for dev_file in sorted(dev_dir.glob("*/usi_dev_*.json")):
        try:
            dev = json.loads(dev_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Pominięto {dev_file}: {e}")
            continue

        pm = dev.get("portal_mapping") or {}
        if len(_portals_present(pm)) <= 1:
            continue

        affected += 1
        new_ids = _split_dev(dev_file, dev, apply, dm)
        total_new += len(new_ids)

    mode = "ZASTOSOWANIE ZMIAN" if apply else "DRY-RUN"
    print(f"\n=== {mode} ===")
    print(f"Pliki do podziału: {affected}")
    if apply:
        print(f"Nowych plików per-portal: {total_new}")
    else:
        print("Uruchom z --apply żeby zastosować zmiany.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    split_multi_portal_devs(Path(USI_DEV_DIR), apply=args.apply)


if __name__ == "__main__":
    main()
