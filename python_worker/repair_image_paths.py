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
    if not d.is_dir():
        return []
    rel = d.relative_to(DROPBOX_PATH)
    return sorted(
        f"/{rel}/{p.name}"
        for p in d.iterdir()
        if p.suffix.lower() in _IMG_EXT and not p.name.startswith(".")
    )


def _find_by_filename(filename: str, public_usi_dir: Path) -> Path | None:
    """Szuka pliku o dokładnej nazwie w całym drzewie public_usi_dir."""
    hits = list(public_usi_dir.glob(f"*/*/{filename}"))
    return hits[0].parent if hits else None


def _find_by_cdn_stem(image_urls: list, public_usi_dir: Path) -> Path | None:
    """Wyciąga stem CDN z pierwszego URL i szuka pliku na dysku."""
    for url in image_urls:
        stem = url.split("/files/")[-1].split("/image")[0]
        if not stem or "/" in stem:
            continue
        for ext in _IMG_EXT:
            hits = list(public_usi_dir.glob(f"*/*/{stem}{ext}"))
            if hits:
                return hits[0].parent
    return None


def _find_by_inv_prefix(inv_slug: str, dev_slug: str, public_usi_dir: Path) -> Path | None:
    """Szuka katalogu w obrębie dev_slug którego nazwa zaczyna się od inv_slug."""
    best_dir: Path | None = None
    best_count = 0
    dev_dir = public_usi_dir / dev_slug
    if not dev_dir.is_dir():
        return None
    for d in dev_dir.iterdir():
        if d.is_dir() and d.name.startswith(inv_slug):
            count = sum(1 for p in d.iterdir() if p.suffix.lower() in _IMG_EXT)
            if count > best_count:
                best_count = count
                best_dir = d
    return best_dir if best_count > 0 else None


def _find_by_exact_inv_slug(inv_slug: str, public_usi_dir: Path) -> Path | None:
    """Szuka katalogu o dokładnej nazwie inv_slug pod dowolnym dev w public_usi_dir."""
    best_dir: Path | None = None
    best_count = 0
    for dev_dir in public_usi_dir.iterdir():
        if not dev_dir.is_dir():
            continue
        candidate = dev_dir / inv_slug
        if candidate.is_dir():
            count = sum(1 for p in candidate.iterdir() if p.suffix.lower() in _IMG_EXT)
            if count > best_count:
                best_count = count
                best_dir = candidate
    return best_dir if best_count > 0 else None


def _resolve_paths(
    raw_paths: list[str],
    image_urls: list[str],
    dev_slug: str,
    inv_slug: str,
    public_usi_dir: Path,
    global_index: dict
) -> tuple[list[str], str]:
    """
    Zwraca (poprawne_ścieżki, metoda).
    Poprawne_ścieżki to lista /Public/USI/... istniejących na dysku.
    """
    # Krok 1 — zweryfikuj istniejące ścieżki
    valid = [p for p in raw_paths if (DROPBOX_PATH / p.lstrip("/")).exists()]
    if valid:
        return valid, "existing"

    # Krok 2 — szukaj po nazwie pliku (przeniesienie 1:1)
    for p in raw_paths:
        filename = Path(p).name
        bname = filename.rsplit(".", 1)[0]
        if bname in global_index:
            found_dir = Path(DROPBOX_PATH) / global_index[bname][0].lstrip("/")
            return _list_images(found_dir.parent), "by_filename"

    # Krok 3 — szukaj po stemie CDN z image_urls
    for url in image_urls:
        stem = url.split("/files/")[-1].split("/image")[0]
        if not stem or "/" in stem:
            continue
        if stem in global_index:
            found_dir = Path(DROPBOX_PATH) / global_index[stem][0].lstrip("/")
            return _list_images(found_dir.parent), "by_cdn_stem"

    # Krok 4 — dokładne dopasowanie inv_slug pod dowolnym dev (inwestycja przeniesiona)
    found_dir = _find_by_exact_inv_slug(inv_slug, public_usi_dir)
    if found_dir:
        return _list_images(found_dir), "by_exact_inv_slug"

    # Krok 5 — szukaj po prefiksie inv_slug w obrębie dev_slug (niestandardowe nazwy plików)
    found_dir = _find_by_inv_prefix(inv_slug, dev_slug, public_usi_dir)
    if found_dir:
        return _list_images(found_dir), "by_prefix"

    return [], "not_found"


def repair(apply: bool = False) -> dict:
    data_dir = Path(USI_DATA_DIR)
    public_usi_dir = Path(PUBLIC_USI_DIR)

    import os
    logger.info("Budowanie globalnego indeksu plików z /Public/USI ...")
    global_index = {}
    for root, dirs, files in os.walk(public_usi_dir):
        for file in files:
            if file.startswith("."):
                continue
            bname = file.rsplit(".", 1)[0]
            if bname not in global_index:
                global_index[bname] = []
            rel_path = os.path.relpath(os.path.join(root, file), public_usi_dir)
            global_index[bname].append(f"/Public/USI/{rel_path}")
    logger.info(f"Zbudowano indeks dla {sum(len(v) for v in global_index.values())} plików.")

    stats = {"ok": 0, "fixed": 0, "not_found": 0}
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
        img_list_str = d.get("ratings", {}).get("imgList", "")
        image_urls = d.get("image_urls", [])

        # Jeśli image_paths już są w całości czynne — nic nie rób
        if existing_paths and all((DROPBOX_PATH / p.lstrip("/")).exists() for p in existing_paths):
            stats["ok"] += 1
            continue

        # Zbierz kandydatów z imgList (image_paths są puste lub mają zepsute ścieżki)
        img_list_paths = [p.strip() for p in img_list_str.split(",") if p.strip()] if img_list_str else []
        raw_paths = list(dict.fromkeys(existing_paths + img_list_paths))

        corrected, method = _resolve_paths(raw_paths, image_urls, dev_slug, inv_slug, public_usi_dir, global_index)

        if not corrected:
            stats["not_found"] += 1
            fixes.append({"slug": f"{dev_slug}/{inv_slug}", "method": "not_found", "old": existing_paths[:2]})
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
            count = inv_index.rebuild(data_dir, public_usi_dir)
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
