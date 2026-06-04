"""
repair_image_paths.py — naprawia image_paths w usi_*.json

Strategia dla każdej inwestycji:
  1. Zbierz kandydatów: image_paths + imgList z ratings
  2. Zweryfikuj które ścieżki istnieją na dysku
  3. Dla nieistniejących — szukaj pliku:
     a) po nazwie pliku (bezpośrednie przeniesienie)
     b) po stemie CDN z image_urls (Otodom)
     c) po prefiksie inv_slug w obrębie dev_slug (niestandardowe nazwy plików)
  4. Zapisz poprawione image_paths do usi_*.json + zaktualizuj indeks

Użycie:
    python3 -m python_worker.repair_image_paths            # dry-run
    python3 -m python_worker.repair_image_paths --apply    # zapis
"""
import argparse
import json
import logging
from pathlib import Path

from python_worker.config import DROPBOX_PATH, PUBLIC_USI_DIR, USI_DATA_DIR

logger = logging.getLogger(__name__)
_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _list_images(d: Path) -> list[str]:
    """Zwraca posortowaną listę /Public/USI/... ścieżek dla katalogu d."""
    if not d or not d.is_dir():
        return []
    try:
        # Try to find PUBLIC_USI_DIR in the path
        import os
        from python_worker.config import PUBLIC_USI_DIR
        rel = os.path.relpath(d, Path(PUBLIC_USI_DIR).parent)
        return sorted(
            f"/{rel}/{p.name}"
            for p in d.iterdir()
            if p.suffix.lower() in _IMG_EXT and not p.name.startswith(".")
        )
    except Exception:
        return []


def _resolve_paths(
    portal: str,
    portal_id: str,
    raw_paths: list[str],
    tech_manager: any
) -> tuple[list[str], str]:
    """
    Zwraca (poprawne_ścieżki, metoda).
    Wykorzystuje TechnicalDataManager do deterministycznej rezolucji.
    """
    if not portal or not portal_id or not tech_manager:
        return [], "missing_id"

    # Deterministyczna ścieżka z biblioteki
    found_dir = tech_manager.get_image_path(portal, str(portal_id))
    
    if found_dir and found_dir.is_dir():
        images = _list_images(found_dir)
        if images:
            return images, "deterministic"

    return [], "not_found"


def repair(apply: bool = False) -> dict:
    data_dir = Path(USI_DATA_DIR)
    
    from python_worker.config import get_scraper_config
    from usi_scrapers.manager import TechnicalDataManager
    config = get_scraper_config()
    tech_manager = TechnicalDataManager(config) if config else None

    stats = {"ok": 0, "fixed": 0, "not_found": 0, "missing_id": 0}
    fixes: list[dict] = []

    for usi_file in sorted(data_dir.glob("*/*/usi_*.json")):
        try:
            d = json.loads(usi_file.read_text())
        except Exception as e:
            logger.warning(f"Nie mogę odczytać {usi_file}: {e}")
            continue

        dev_slug = usi_file.parent.parent.name
        inv_slug = usi_file.parent.name
        existing_paths = d.get("image_paths") or []
        
        # Determine portal/portal_id
        portal = d.get("portal")
        portal_id = d.get("portal_id")
        if not portal or not portal_id:
            sources = d.get("sources") or {}
            for p in ("rp", "oto", "to"):
                if p in sources and sources[p].get("id"):
                    portal = p
                    portal_id = sources[p].get("id")
                    break

        # Jeśli image_paths już są w całości czynne — nic nie rób
        from python_worker.config import DROPBOX_PATH
        if existing_paths and all((DROPBOX_PATH / p.lstrip("/")).exists() for p in existing_paths):
            stats["ok"] += 1
            continue

        corrected, method = _resolve_paths(portal, portal_id, existing_paths, tech_manager)

        if not corrected:
            if method == "missing_id":
                stats["missing_id"] += 1
            else:
                stats["not_found"] += 1
            fixes.append({"slug": f"{dev_slug}/{inv_slug}", "method": method, "old": existing_paths[:2]})
            continue

        stats["fixed"] += 1
        fixes.append({
            "slug": f"{dev_slug}/{inv_slug}",
            "method": method,
            "old_count": len(existing_paths),
            "new_count": len(corrected),
        })

        if apply:
            d["image_paths"] = corrected
            d["images_count"] = len(corrected)
            usi_file.write_text(json.dumps(d, ensure_ascii=False, indent=2))

    if apply:
        try:
            import python_worker.investment_index as inv_index
            from python_worker.config import PUBLIC_USI_DIR
            count = inv_index.rebuild(data_dir, Path(PUBLIC_USI_DIR))
            logger.info(f"Indeks przebudowany: {count}")
        except Exception as e:
            logger.warning(f"Błąd przebudowy indeksu: {e}")

    return {"stats": stats, "fixes": fixes}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Napraw image_paths w usi_*.json")
    parser.add_argument("--apply", action="store_true", help="Zapisz zmiany (domyślnie dry-run)")
    args = parser.parse_args()

    result = repair(apply=args.apply)
    stats = result["stats"]
    fixes = result["fixes"]

    print(f"\n{'=== DRY-RUN ===' if not args.apply else '=== ZASTOSOWANO ==='}")
    print(f"  OK (bez zmian):    {stats['ok']}")
    print(f"  Naprawione:        {stats['fixed']}")
    print(f"  Nie znaleziono:    {stats['not_found']}  (wymagają update-inv)")

    if fixes:
        by_method: dict[str, list] = {}
        for f in fixes:
            by_method.setdefault(f["method"], []).append(f)

        print("\nNaprawione wg metody:")
        for method, items in sorted(by_method.items()):
            print(f"  {method}: {len(items)}")
            for item in items[:3]:
                print(f"    {item['slug']}")
            if len(items) > 3:
                print(f"    ... i {len(items)-3} więcej")
