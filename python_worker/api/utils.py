import re
import math
from pathlib import Path

# Exporting components extracted to amenity_scorer
from python_worker.services.amenity_scorer import (
    CATS as _CATS,
    USI_STATUSES,
    load_wyrozniki as _load_wyrozniki,
    compute_amenity_score as _compute_amenity_score,
    suggest_udogodnienia as _suggest_udogodnienia,
    calculate_ocena_log as _calculate_ocena_log
)

from python_worker.services.investment_loader import (
    find_inv_file as _find_inv_file,
    load_investment as _real_load_investment
)

def _load_investment(*args, **kwargs):
    # Support legacy positional args: (dev_slug, inv_slug)
    if len(args) == 2:
        kwargs['dev_slug'] = args[0]
        kwargs['inv_slug'] = args[1]
    elif len(args) == 1:
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
