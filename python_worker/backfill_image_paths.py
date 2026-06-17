import json
import logging
import re
from pathlib import Path
import sys

# Dodanie katalogu głównego do ścieżki (umożliwia import z python_worker)
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_PHOTO_DIR_RE = re.compile(r'^/api/image/(.+)/[^/]+$')
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _extract_dir_from_photos(photos: list) -> str | None:
    """Wyciąga pełną ścieżkę do katalogu ze zdjęciami z pierwszego poprawnego URL w polu photos.
    Obsługuje ścieżki 2-, 3- i 4-poziomowe."""
    for url in photos:
        if not isinstance(url, str):
            continue
        m = _PHOTO_DIR_RE.match(url)
        if m:
            return m.group(1)
    return None


def _scan_image_dir(image_dir: Path, dir_rel: str) -> list[str]:
    """Zwraca posortowaną listę ścieżek /Public/USI/{dir_rel}/{file} dla plików w katalogu.
    dir_rel może być jedno- lub wielopoziomowy (np. 'dev/inv' lub 'dev/sub/inv')."""
    paths = []
    try:
        for item in sorted(image_dir.iterdir()):
            if item.is_file() and item.suffix.lower() in _IMG_EXTS:
                paths.append(f"/Public/USI/{dir_rel}/{item.name}")
    except OSError as e:
        logger.warning(f"Cannot scan {image_dir}: {e}")
    return paths


def run_backfill(data_dir: Path, usi_dir: Path) -> tuple[int, int]:
    count_updated = 0
    count_errors = 0

    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return 0, 0

    for dev_dir in data_dir.iterdir():
        if not dev_dir.is_dir() or dev_dir.name.startswith("_"):
            continue

        for inv_dir in dev_dir.iterdir():
            if not inv_dir.is_dir():
                continue

            dev_slug = dev_dir.name
            inv_slug = inv_dir.name

            for usi_file in inv_dir.glob("usi_*.json"):
                try:
                    with open(usi_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    changed = False

                    # 1. Czyszczenie image_urls z lokalnych ścieżek
                    urls = data.get("image_urls", [])
                    clean_urls = [u for u in urls if isinstance(u, str) and u.startswith("http")]
                    if len(clean_urls) != len(urls):
                        data["image_urls"] = clean_urls
                        changed = True

                    # 2. Rekonstrukcja image_paths
                    current_paths = data.get("image_paths", [])

                    # 2a. Jeśli image_paths już niepuste — sprawdź tylko czy nie wskazują
                    #     na nieistniejące pliki (sanity check); jeśli ok, pomijamy.
                    if current_paths:
                        valid = [
                            p for p in current_paths
                            if isinstance(p, str)
                            and "Public/USI/" in p
                            and (usi_dir / p.split("Public/USI/")[-1].lstrip("/")).exists()
                        ]
                        if len(valid) != len(current_paths):
                            data["image_paths"] = valid
                            data["images_count"] = len(valid)
                            changed = True
                        # image_paths nadal niepuste — przechodzimy dalej
                        if data.get("image_paths"):
                            if changed:
                                with open(usi_file, "w", encoding="utf-8") as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                count_updated += 1
                            continue

                    # 2b. image_paths puste — szukamy plików na dysku

                    # Krok 1: Sprawdź katalog pod bieżącym slugiem
                    image_paths = _scan_image_dir(usi_dir / dev_slug / inv_slug, f"{dev_slug}/{inv_slug}")

                    # Krok 2 (FALLBACK): Katalog pod bieżącym slugiem nie ma plików —
                    # wyciągnij pełną ścieżkę katalogu z pola photos i spróbuj stamtąd.
                    if not image_paths:
                        photos = data.get("photos", [])
                        if photos:
                            photo_dir_rel = _extract_dir_from_photos(photos)
                            if photo_dir_rel and photo_dir_rel != f"{dev_slug}/{inv_slug}":
                                fallback_dir = usi_dir / photo_dir_rel
                                image_paths = _scan_image_dir(fallback_dir, photo_dir_rel)
                                if image_paths:
                                    logger.info(
                                        f"[FALLBACK] {dev_slug}/{inv_slug}: odbudowano {len(image_paths)} ścieżek "
                                        f"z alternatywnego katalogu {photo_dir_rel}"
                                    )

                    if image_paths != current_paths:
                        data["image_paths"] = image_paths
                        data["images_count"] = len(image_paths)
                        changed = True

                    if changed:
                        with open(usi_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        count_updated += 1
                        logger.info(
                            f"Updated {dev_slug}/{inv_slug} ({usi_file.name}): "
                            f"{len(image_paths)} paths restored."
                        )

                except Exception as e:
                    logger.error(f"Error processing {usi_file}: {e}")
                    count_errors += 1

    return count_updated, count_errors


def main():
    data_dir = Path(USI_DATA_DIR)
    usi_dir = Path(PUBLIC_USI_DIR)

    logger.info(f"Starting image_paths backfill...")
    logger.info(f"USIdata: {data_dir}")
    logger.info(f"USI: {usi_dir}")

    updated, errors = run_backfill(data_dir, usi_dir)
    logger.info(f"Backfill complete. Updated {updated} files. Errors: {errors}")


if __name__ == "__main__":
    main()
