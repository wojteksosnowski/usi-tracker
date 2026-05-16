"""
clean_portal_mappings.py — Czyści portal_mapping w plikach usi_dev_*.json.

Zasada: usi_dev_*.json odpowiada 1:1 plikom raw_*.json w tym samym katalogu.
Wpis portal_mapping dla portalu bez odpowiadającego raw_{portal}_{slug}.json
jest wynikiem błędnego kopiowania podczas scalania i powinien być usunięty.

Dry-run (domyślny):
    python3 -m python_worker.clean_portal_mappings

Zastosowanie zmian:
    python3 -m python_worker.clean_portal_mappings --apply
"""

import argparse
import json
import logging
from pathlib import Path

from python_worker.config import USI_DEV_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PORTALS = ("rp", "oto", "to")


def _raw_exists(dev_dir: Path, slug: str, portal: str) -> bool:
    return (dev_dir / f"raw_{portal}_{slug}.json").exists()


def clean_portal_mappings(dev_dir: Path, apply: bool) -> None:
    affected = 0
    total_removed = 0

    for dev_file in sorted(dev_dir.glob("*/usi_dev_*.json")):
        slug = dev_file.parent.name
        try:
            dev = json.loads(dev_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Pominięto {dev_file}: {e}")
            continue

        pm = dev.get("portal_mapping") or {}
        removed = []

        for portal in PORTALS:
            if pm.get(portal) and not _raw_exists(dev_file.parent, slug, portal):
                removed.append((portal, pm[portal]))

        if not removed:
            continue

        affected += 1
        total_removed += len(removed)
        print(f"  [{slug}]")
        for portal, val in removed:
            print(f"    − portal_mapping.{portal} = {str(val)[:80]}")

        if apply:
            for portal, _ in removed:
                pm[portal] = None
            dev["portal_mapping"] = pm
            dev_file.write_text(json.dumps(dev, indent=2, ensure_ascii=False), encoding="utf-8")

    mode = "ZASTOSOWANIE ZMIAN" if apply else "DRY-RUN"
    print(f"\n=== {mode} ===")
    print(f"Deweloperzy z osieroconym portal_mapping: {affected}")
    print(f"Usuniętych wpisów: {total_removed}")

    if not apply:
        print("Uruchom z --apply żeby zastosować zmiany.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    clean_portal_mappings(Path(USI_DEV_DIR), apply=args.apply)


if __name__ == "__main__":
    main()
