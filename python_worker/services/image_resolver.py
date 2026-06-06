import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def resolve_images(usi: dict, inv_dir: Path = None, public_usi_dir: Path = None, resources: dict = None, fast_index: bool = False) -> list[str]:
    """
    Authoritative image resolver.
    Checks if images exist locally. If so, returns /api/image/... relative path.
    If not, returns the original CDN URL from image_urls.
    """
    from python_worker.config import PUBLIC_USI_DIR
    if public_usi_dir is None:
        public_usi_dir = Path(PUBLIC_USI_DIR)
    
    # If fast_index is True, we just want a quick list, preferably what's already there
    if fast_index and usi.get("photos"):
        return usi["photos"]

    image_paths = usi.get("image_paths", [])
    image_urls = usi.get("image_urls", [])
    
    # Fallback to legacy imgList if image_paths is empty
    if not image_paths:
        img_list_str = usi.get("ratings", {}).get("imgList", "")
        if img_list_str:
            image_paths = [p.strip() for p in img_list_str.split(",") if p.strip()]

    if not image_paths:
        return usi.get("photos", [])

    resolved = []
    
    # Pair paths with URLs
    for i, p_str in enumerate(image_paths):
        # Convert path string to absolute Path object to check existence
        # p_str is usually "Public/USI/dev-slug/inv-slug/file.jpg"
        
        rel_p = p_str.split('Public/USI/')[-1].lstrip('/')
        abs_p = public_usi_dir / rel_p
        
        if abs_p.exists() and abs_p.is_file():
            # File exists locally - serve via our API
            resolved.append(f"/api/image/{rel_p}")
        elif i < len(image_urls) and str(image_urls[i]).startswith("http"):
            # File missing locally - use CDN URL
            resolved.append(image_urls[i])
        else:
            # Last resort: just keep the API path and let serve_image return 404
            resolved.append(f"/api/image/{rel_p}")
            
    return resolved
