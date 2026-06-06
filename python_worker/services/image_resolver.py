import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Dopuszczalne znaki: litery, cyfry, myślniki, podkreślniki, kropki. Żadnych ścieżek!
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+$')

def resolve_images(usi: dict, inv_dir: Path, public_usi_dir: Path, resources: dict = None, fast_index: bool = False) -> list[str]:
    """Resolves images to clean relative paths using a strict filename whitelist."""
    raw = usi.get("image_paths") or [p.strip() for p in usi.get("ratings", {}).get("imgList", "").split(",") if p.strip()]
    
    resolved = []
    if raw:
        for p in raw:
            # SZYBKI BEZPIECZNIK: Jeśli ścieżka jest adresem URL, pomiń ją bezwzględnie
            if str(p).startswith(("http://", "https://")):
                logger.warning( f"Wykryto wyciek surowego URL w image_paths: {p}. Pomijanie.")
                continue

            # 1. Extract path part relative to Public/USI/
            if "Public/USI/" in p:
                path_part = p.split('Public/USI/')[-1].lstrip('/')
            else:
                path_part = p.lstrip('/')
            
            # 2. Extract filename for regex validation
            filename = path_part.split('/')[-1]
            
            # 3. Walidacja wzorcem
            if not SAFE_FILENAME_PATTERN.match(filename):
                logger.debug(f"Odrzucono niebezpieczną nazwę pliku: {filename}")
                continue
                
            # 4. Sprawdzenie istnienia przy użyciu pełnej ścieżki relatywnej
            full_path = public_usi_dir / path_part
            if not full_path.exists():
                logger.debug(f"Image file not found on disk: {full_path}")
                continue
                
            resolved.append(f"/api/image/{path_part}")
            
    return resolved if resolved else []
