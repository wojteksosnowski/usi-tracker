import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def resolve_images(usi: dict, inv_dir: Path, public_usi_dir: Path, resources: dict = None, fast_index: bool = False) -> list[str]:
    """Resolves images to clean relative paths, ignoring invalid or base64 data and non-existent files."""
    raw = usi.get("image_paths") or [p.strip() for p in usi.get("ratings", {}).get("imgList", "").split(",") if p.strip()]
    
    resolved = []
    if raw:
        for p in raw:
            # 1. Clean path: extract relative part
            if "Public/USI/" in p:
                path_part = p.split('Public/USI/')[-1]
            else:
                path_part = p
            path_part = path_part.lstrip('/')
            
            # 2. Heuristic check to discard malformed/base64 strings
            # A valid relative image path should contain at least one '/' and one '.' (extension)
            if "/" not in path_part or "." not in path_part or len(path_part) > 255:
                logger.debug(f"Skipping malformed image path: {path_part}")
                continue
                
            # 3. Check existence
            full_path = public_usi_dir / path_part
            if not full_path.exists():
                logger.debug(f"Image file not found on disk, skipping: {full_path}")
                continue
                
            resolved.append(f"/api/image/{path_part}")
            
    return resolved if resolved else []
