"""
backfill_inv_dev_ids.py — Uzupełnia vendor_id / agency_id w istniejących usi_*.json.

Dla każdego pliku usi_*.json który ma sources.rp lub sources.oto ale brakuje
identyfikatora dewelopera — odczytuje odpowiedni raw_*.json i wyciąga ID.

Dry-run (domyślny):
    python3 -m python_worker.backfill_inv_dev_ids

Zastosowanie zmian:
    python3 -m python_worker.backfill_inv_dev_ids --apply
"""
import argparse
import json
import logging
from pathlib import Path

from python_worker.config import USI_DATA_DIR
from python_worker.adapters import _get_val

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _extract_rp_vendor_id(raw_rp: Path) -> str | None:
    try:
        raw = json.loads(raw_rp.read_text(encoding="utf-8"))
        vendor = _get_val(raw, "vendor")
        if isinstance(vendor, dict):
            vid = _get_val(vendor, "id")
            if vid:
                return str(vid)
    except Exception as e:
        logger.warning("Nie można odczytać %s: %s", raw_rp, e)
    return None


def _extract_oto_agency_id(raw_oto: Path) -> str | None:
    try:
        raw = json.loads(raw_oto.read_text(encoding="utf-8"))
        ad = raw.get("ad") or raw
        agency = ad.get("agency") or {}
        aid = agency.get("id") or (ad.get("owner") or {}).get("id")
        if aid:
            return str(aid)
    except Exception as e:
        logger.warning("Nie można odczytać %s: %s", raw_oto, e)
    return None


def backfill(data_dir: Path, apply: bool) -> None:
    patched = skipped = missing_raw = 0

    for dev_dir in sorted(data_dir.iterdir()):
        if not dev_dir.is_dir() or dev_dir.name.startswith("."):
            continue
        dev_slug = dev_dir.name

        for inv_dir in sorted(dev_dir.iterdir()):
            if not inv_dir.is_dir() or inv_dir.name.startswith("."):
                continue
            inv_slug = inv_dir.name

            usi_files = list(inv_dir.glob("usi_*.json"))
            if not usi_files:
                continue
            usi_file = usi_files[0]

            try:
                usi = json.loads(usi_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Pominięto %s: %s", usi_file, e)
                skipped += 1
                continue

            src = usi.get("sources") or {}
            changed = False

            # RP: fill vendor_id
            if src.get("rp") is not None and not src["rp"].get("vendor_id"):
                raw_rp = inv_dir / f"raw_rp_{inv_slug}.json"
                if raw_rp.exists():
                    vid = _extract_rp_vendor_id(raw_rp)
                    if vid:
                        src["rp"]["vendor_id"] = vid
                        changed = True
                        logger.info("[rp] %s/%s → vendor_id=%s", dev_slug, inv_slug, vid)
                else:
                    missing_raw += 1

            # OTO: fill agency_id
            if src.get("oto") is not None and not src["oto"].get("agency_id"):
                raw_oto = inv_dir / f"raw_oto_{inv_slug}.json"
                if raw_oto.exists():
                    aid = _extract_oto_agency_id(raw_oto)
                    if aid:
                        src["oto"]["agency_id"] = aid
                        changed = True
                        logger.info("[oto] %s/%s → agency_id=%s", dev_slug, inv_slug, aid)
                else:
                    missing_raw += 1

            if changed:
                patched += 1
                if apply:
                    usi["sources"] = src
                    usi_file.write_text(json.dumps(usi, indent=2, ensure_ascii=False),
                                        encoding="utf-8")
            else:
                skipped += 1

    mode = "ZASTOSOWANIE ZMIAN" if apply else "DRY-RUN"
    print(f"\n=== {mode} ===")
    print(f"Pliki do aktualizacji: {patched}")
    print(f"Pominięte (już OK lub błąd): {skipped}")
    print(f"Brak raw file: {missing_raw}")
    if not apply:
        print("Uruchom z --apply żeby zastosować zmiany.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    backfill(Path(USI_DATA_DIR), apply=args.apply)


if __name__ == "__main__":
    main()
