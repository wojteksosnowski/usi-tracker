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
    
    from python_worker.services.investment_loader import load_investment
    return load_investment(**kwargs)

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

def filter_investments(investments: list, filters: dict) -> list:
    """Universal investment filtering logic used across different API endpoints."""
    from python_worker.services.amenity_scorer import calculate_ocena_log
    
    filtered = []
    
    # Pre-process filters to handle both string (from request.args) and direct types
    search = str(filters.get("search", "")).lower()
    only_unreviewed = str(filters.get("onlyUnreviewed")).lower() == "true"
    only_no_photos = str(filters.get("onlyNoPhotos")).lower() == "true"
    status = filters.get("status")
    dev_slug = filters.get("dev") or filters.get("developer_slug")
    
    sources = filters.get("sources", [])
    if isinstance(sources, str): sources = sources.upper().split(",") if sources else []
    
    segments = filters.get("segments", [])
    if isinstance(segments, str): segments = segments.split(",") if segments else []
    
    cities = filters.get("cities", [])
    if isinstance(cities, str): cities = cities.lower().split(",") if cities else []
    elif not cities and filters.get("city"): cities = [filters.get("city").lower()]

    min_rating = filters.get("min_rating")
    near = filters.get("near") # Expected format: {coords: [lat, lon], radius: float}

    for inv in investments:
        if not inv: continue
        
        # 1. Reviewed / Unreviewed
        if only_unreviewed and inv.get("reviewed") is True: continue
        
        # 2. No Photos
        if only_no_photos and len(inv.get("photos", [])) > 0: continue
        
        # 3. Status
        if status and inv.get("status") != status: continue
        
        # 4. Developer
        if dev_slug and inv.get("developer_slug") != dev_slug: continue
        
        # 5. Cities (Matches city, address, or district)
        if cities:
            inv_city = (inv.get("city") or "").lower()
            inv_addr = (inv.get("address") or "").lower()
            inv_distr = (inv.get("district") or "").lower()
            if not any(c in inv_city or c in inv_addr or c in inv_distr for c in cities):
                continue
        
        # 6. Segments
        if segments and inv.get("segment") not in segments: continue
        
        # 7. Sources (Portals)
        if sources:
            inv_sources = inv.get("sources", {}).keys()
            if not any(s.lower() in [isrc.lower() for isrc in inv_sources] for s in sources):
                continue

        # 8. Min Rating
        if min_rating:
            score = calculate_ocena_log(inv.get("ratings", {}))
            if score is None or score < float(min_rating):
                continue

        # 9. Proximity (Near)
        if near:
            center = near.get("coords")
            radius = near.get("radius", 5)
            if center and inv.get("coords"):
                dist = _calculate_distance(center[0], center[1], inv["coords"][0], inv["coords"][1])
                if dist > radius:
                    continue

        # 10. Search (General text)
        if search:
            match = False
            for field in ["name", "developer", "address", "city", "usi_inv_id"]:
                if search in str(inv.get(field, "")).lower():
                    match = True
                    break
            if not match: continue
            
        filtered.append(inv)
        
    return filtered

def _calculate_distance(lat1, lon1, lat2, lon2):
    """Oblicza odległość między dwoma punktami (Haversine)."""
    R = 6371  # Promień Ziemi w km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
