import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Dopuszczalne znaki: litery, cyfry, myślniki, podkreślniki, kropki. Żadnych ścieżek!
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+$')

# Wyciąganie {dev}/{inv} z URL-i pola photos
_PHOTO_URL_RE = re.compile(r'^/api/image/([^/]+)/([^/]+)/(.+)$')
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _resolve_from_paths(raw: list, public_usi_dir: Path, deleted_paths: set) -> list[str]:
    """Resolves a raw list of /Public/USI/… paths into clean /api/image/… paths."""
    resolved = []
    for p in raw:
        if str(p).startswith(("http://", "https://")):
            logger.warning(f"Wykryto wyciek surowego URL w image_paths: {p}. Pomijanie.")
            continue

        if "Public/USI/" in p:
            path_part = p.split('Public/USI/')[-1].lstrip('/')
        else:
            path_part = p.lstrip('/')

        filename = path_part.split('/')[-1]
        if not SAFE_FILENAME_PATTERN.match(filename):
            logger.debug(f"Odrzucono niebezpieczną nazwę pliku: {filename}")
            continue

        full_path = public_usi_dir / path_part
        if not full_path.exists():
            logger.debug(f"Image file not found on disk: {full_path}")
            continue

        resolved_path = f"/api/image/{path_part}"
        if deleted_paths and resolved_path in deleted_paths:
            continue

        resolved.append(resolved_path)
    return resolved


def _resolve_from_photos_fallback(photos: list, public_usi_dir: Path, deleted_paths: set) -> list[str]:
    """
    FALLBACK: Gdy image_paths jest puste, wyciąga dev/inv slug z pola photos
    i skanuje fizyczny katalog USI, odbudowując poprawne ścieżki.
    Używany gdy zdjęcia istnieją pod starym/innym slugiem.
    """
    if not photos:
        return []

    # Wyciągnij unikalny (dev_slug, inv_slug) z pierwszego poprawnego photos URL
    photo_dev, photo_inv = None, None
    for url in photos:
        if not isinstance(url, str):
            continue
        m = _PHOTO_URL_RE.match(url)
        if m:
            photo_dev, photo_inv = m.group(1), m.group(2)
            break

    if not photo_dev or not photo_inv:
        return []

    disk_dir = public_usi_dir / photo_dev / photo_inv
    if not disk_dir.is_dir():
        return []

    resolved = []
    try:
        for item in sorted(disk_dir.iterdir()):
            if not item.is_file() or item.suffix.lower() not in _IMG_EXTS:
                continue
            filename = item.name
            if not SAFE_FILENAME_PATTERN.match(filename):
                continue
            resolved_path = f"/api/image/{photo_dev}/{photo_inv}/{filename}"
            if deleted_paths and resolved_path in deleted_paths:
                continue
            resolved.append(resolved_path)
    except OSError as e:
        logger.warning(f"Cannot scan fallback dir {disk_dir}: {e}")

    if resolved:
        logger.info(
            f"[image_resolver] FALLBACK: odbudowano {len(resolved)} ścieżek "
            f"z alternatywnego katalogu {photo_dev}/{photo_inv}"
        )
    return resolved


def resolve_images(usi: dict, inv_dir: Path, public_usi_dir: Path, resources: dict = None, fast_index: bool = False, deleted_paths: set = None) -> list[str]:
    """Resolves images to clean relative paths using a strict filename whitelist and filters out deleted paths.

    Priority:
    1. image_paths field in usi JSON (canonical, /Public/USI/… paths)
    2. ratings.imgList field (legacy fallback)
    3. FALLBACK: scan disk using dev/inv slug extracted from photos field URLs
    """
    ratings_dict = usi.get("ratings") or {}
    imgList = ratings_dict.get("imgList") or ""
    raw = usi.get("image_paths") or [p.strip() for p in imgList.split(",") if p.strip()]

    deleted_paths = deleted_paths or set()

    if raw:
        resolved = _resolve_from_paths(raw, public_usi_dir, deleted_paths)
        if resolved:
            return resolved

    # FALLBACK: image_paths pusty lub wszystkie ścieżki odrzucone — spróbuj z pola photos
    photos = usi.get("photos") or []
    return _resolve_from_photos_fallback(photos, public_usi_dir, deleted_paths)
