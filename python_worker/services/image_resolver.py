import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}

def resolve_images(usi: dict, inv_dir: Path, public_usi_dir: Path, resources: dict | None = None, fast_index: bool = False) -> list[str]:
    """
    Resolves authoritative image paths for an investment.
    Prioritizes explicit paths saved in JSON over directory scanning.
    """
    images = []
    
    # 1. Priority: Recorded paths (imgList from ratings or image_paths)
    image_paths_raw = usi.get("image_paths") or []
    img_list_str = usi.get("ratings", {}).get("imgList")
    
    if img_list_str and isinstance(img_list_str, str):
        image_paths_raw = [p.strip() for p in img_list_str.split(",") if p.strip()]
        
    if image_paths_raw:
        from python_worker.config import DROPBOX_PATH
        for p in image_paths_raw:
            p_clean = p.lstrip("/")
            if not fast_index and not (DROPBOX_PATH / p_clean).exists():
                continue
            
            if p_clean.startswith("Public/USI/"):
                suffix = p_clean[len("Public/USI/"):]
                images.append("/api/image/" + suffix)
        images = sorted(list(set(images)))

    # 2. Fallback or Supplement: Directory scan
    if not fast_index:
        img_dir = resources.get("images_dir") if resources else None
            
        def _scan(d: Path) -> list:
            if not d or not d.is_dir(): return []
            rel_dir = d.relative_to(public_usi_dir)
            return sorted(
                f"/api/image/{rel_dir}/{p.name}"
                for p in d.iterdir()
                if p.suffix.lower() in _IMG_EXT and not p.name.startswith('.')
            )

        if not images and img_dir:
            images.extend(_scan(img_dir))

        # The legacy global CDN filename glob scan has been removed.
        # It caused severe performance hangs (O(N) full drive scan per missing image url)
        # and violated the ID-only architecture. Fallback to portal URLs is handled below.
    elif not images:
        # Legacy fallback for index
        pass

    # 3. Supplement with portal URLs
    portal_urls = usi.get("image_urls", [])
    if not fast_index:
        for url in portal_urls:
            url_filename = url.split("/")[-1].split("?")[0]
            if not any(url_filename in img for img in images):
                images.append(url)
    elif not images:
        images = portal_urls[:1]

    return images

