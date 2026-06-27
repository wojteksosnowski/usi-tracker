import re
import math
import json
from pathlib import Path
from datetime import datetime, timezone

# Constants for USI
CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia']
USI_STATUSES = ['Brak', 'AI', 'Wstępna', 'Poszerzona', 'Pełna', 'Aktualizacja', 'Ukończona', 'Niedostateczne dane']

def now_utc(): 
    return datetime.now(tz=timezone.utc)

def to_iso(dt): 
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(path: Path): 
    if not path or not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

def _load_investment(system_id: str = None, *args, **kwargs):
    """Wrapper kompatybilności — deleguje do InvestmentRepository."""
    from python_worker.config import get_shared_repository
    sid = system_id or kwargs.get("system_id")
    return get_shared_repository().get_investment_json(sid) if sid else None

def _valid_slug(s: str) -> bool:
    return bool(s) and bool(re.match(r"^[a-zA-Z0-9_-]+$", s))

def _valid_filename(s: str) -> bool:
    if ".." in s: return False
    return bool(s) and bool(re.match(r"^[^/\\]+\.(jpg|jpeg|png|webp|svg)$", s, re.IGNORECASE))

def get_anchor_path(system_id: str) -> Path | None:
    """Resolves the physical Path to the investment anchor file (usi_*.json)."""
    import python_worker.investment_index as inv_index
    from python_worker.config import PUBLIC_USI_DIR
    
    entry = inv_index.get_entry_by_id(system_id)
    if not entry or not entry.get("folder_path"):
        return None
        
    full_folder_path = Path(PUBLIC_USI_DIR).parent / entry["folder_path"]
    usi_files = list(full_folder_path.glob("usi_*.json"))
    return usi_files[0] if usi_files else None

def update_anchor_json(system_id: str, update_fn) -> bool:
    """Reads, updates (via update_fn), and writes back the anchor JSON safely.
    Also synchronizes the hot RAM index.
    """
    import json
    import python_worker.investment_index as inv_index
    
    file_path = get_anchor_path(system_id)
    if not file_path:
        return False
        
    try:
        with open(file_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            
            # Allow update_fn to return False to abort
            if update_fn(data) is False:
                return False
                
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.truncate()
            
        # Update RAM index entry
        entry = inv_index.get_entry_by_id(system_id)
        if entry:
            # Re-sync fields that are commonly updated and synced to RAM
            for field in ["reviewed", "ratings", "status", "user_reports", "comment"]:
                if field in data:
                    entry[field] = data[field]
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"update_anchor_json failed for {system_id}: {e}")
        return False

def _calculate_distance(lat1, lon1, lat2, lon2):
    """Oblicza odległość między dwoma punktami (Haversine)."""
    R = 6371  # Promień Ziemi w km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
