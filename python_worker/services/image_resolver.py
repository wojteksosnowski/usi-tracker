import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def resolve_images(usi: dict, *args, **kwargs) -> list[str]:
    """Radically simplified: trust JSON paths, zero disk scanning."""
    raw = usi.get("image_paths") or [p.strip() for p in usi.get("ratings", {}).get("imgList", "").split(",") if p.strip()]
    if raw: 
        return [f"/api/image/{p.split('Public/USI/')[-1].lstrip('/')}" for p in raw if "Public/USI/" in p]
    return usi.get("photos", [])
