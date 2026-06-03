import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}

def resolve_images(usi: dict, inv_dir: Path, public_usi_dir: Path, dev_slug: str, inv_slug: str, resources: dict | None = None, fast_index: bool = False) -> list[str]:
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
        if resources and resources.get("images_dir"):
            img_dir = resources["images_dir"]
        else:
            img_dir = public_usi_dir / dev_slug / inv_slug
            
        def _scan(d: Path) -> list:
            if not d.is_dir(): return []
            return sorted(
                f"/api/image/{d.parent.name}/{d.name}/{p.name}"
                for p in d.iterdir()
                if p.suffix.lower() in _IMG_EXT and not p.name.startswith('.')
            )

        local_found = []
        for candidate in (img_dir, public_usi_dir / Path(inv_dir).parent.name / inv_slug):
            local_found = _scan(candidate)
            if local_found:
                break
        
        for img in local_found:
            if img not in images:
                images.append(img)

        # Locate by CDN filename from image_urls
        if not images and public_usi_dir.is_dir():
            for url in usi.get("image_urls", []):
                stem = url.split("/files/")[-1].split("/image")[0]
                if not stem or "/" in stem: continue
                hits = list(public_usi_dir.glob(f"*/*/{stem}.*"))
                if hits:
                    images = _scan(hits[0].parent)
                    break
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
