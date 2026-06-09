import re
import math
import json
from pathlib import Path
from datetime import datetime, timezone

# Constants for USI
CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia']
USI_STATUSES = ['Brak', 'AI', 'Wstępna', 'Poszerzona', 'Pełna', 'Aktualizacja', 'Ukończona']

def now_utc(): 
    return datetime.now(tz=timezone.utc)

def to_iso(dt): 
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(path: Path): 
    if not path or not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

def _load_investment(*args, **kwargs):
    # Support positional arg for system_id
    if len(args) == 1:
        kwargs['system_id'] = args[0]
    return _real_load_investment(**kwargs)

def _valid_slug(s: str) -> bool:
    return bool(s) and bool(re.match(r"^[a-zA-Z0-9_-]+$", s))

def _valid_filename(s: str) -> bool:
    if ".." in s: return False
    return bool(s) and bool(re.match(r"^[^/\\]+\.(jpg|jpeg|png|webp|svg)$", s, re.IGNORECASE))

def _calculate_distance(lat1, lon1, lat2, lon2):
    """Oblicza odległość między dwoma punktami (Haversine)."""
    R = 6371  # Promień Ziemi w km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
