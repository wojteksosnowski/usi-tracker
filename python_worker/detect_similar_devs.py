import json
import logging
import math
from pathlib import Path
from python_worker.config import USI_DEV_DIR, USI_DATA_DIR
from python_worker.developer_manager import DeveloperManager
import re

from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def fuzzy_match(s1, s2):
    """Returns similarity ratio between two strings."""
    return SequenceMatcher(None, s1, s2).ratio()

def haversine(lat1, lon1, lat2, lon2):
    """Calculates distance between two points on Earth in meters."""
    R = 6371000  # radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_dev_metadata(dev_slug: str, data_dir: Path):
    """Collects coordinates and delivery dates for all investments of a developer."""
    metadata = []
    dev_path = data_dir / dev_slug
    if not dev_path.exists(): return []
    
    try:
        for inv_dir in dev_path.iterdir():
            if not inv_dir.is_dir(): continue
            usi_file = inv_dir / f"usi_{inv_dir.name}.json"
            if usi_file.exists():
                with open(usi_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    c = data.get("location", {}).get("coords")
                    spec = data.get("specifications", {})
                    year = spec.get("delivery_year")
                    
                    if c and isinstance(c, list) and len(c) == 2:
                        metadata.append({
                            "coords": tuple(c),
                            "year": int(year) if year else None
                        })
    except Exception:
        pass
    return metadata

def normalize_name(name: str) -> str:
    """Normalizes developer name for comparison."""
    if not name: return ""
    n = name.lower()
    # Remove dots to simplify legal forms (e.g. S.A. -> sa, Sp. z o.o. -> sp z oo)
    n = n.replace(".", "")
    # Remove common legal forms and industry words
    n = re.sub(r"\b(spółka|z oo|sa|spk|sp z oo|sc|sj|spj|holding|group|development|investment|investments|invest|nieruchomości|domy|mieszkania|bud|sp|biuro|zarząd|przedsiebiorstwo|przedsiębiorstwo|budowlane|pphu|phu|pbu|zrb|fhu|firma|uslugowo|usługowo|handlowe|uslugowe|usługowe|handlowa|spoldzielnia|spółdzielnia|mieszkaniowa|immobilier|polska|ograniczona|ograniczoną|odpowiedzialnoscia|odpowiedzialnością)\b", "", n)
    # Remove remaining punctuation
    n = re.sub(r"[^\w\s]", "", n)
    # Collapse whitespace
    n = " ".join(n.split())
    return n

def _build_dismissed_cache(dev_dir: Path) -> dict[str, set[str]]:
    """Returns {usi_dev_id → set of dismissed usi_dev_ids} from all dev_master_*.json files."""
    cache: dict[str, set[str]] = {}
    for master_file in dev_dir.glob("*/dev_master_*.json"):
        try:
            master = json.loads(master_file.read_text(encoding="utf-8"))
            owner_id = master.get("master_usi_dev_id")
            if owner_id:
                cache[owner_id] = {
                    d["usi_dev_id"] for d in master.get("dismissed", [])
                    if d.get("usi_dev_id")
                }
        except Exception:
            continue
    return cache


def detect_similar():
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    devs = dm.list_developers()

    dismissed_cache = _build_dismissed_cache(Path(USI_DEV_DIR))

    logger.info(f"Analyzing {len(devs)} developers for similarities (Optimized)...")
    
    # 1. Build Index (Buckets)
    processed = []
    for d in devs:
        slug = d["developer_slug"]
        norm = normalize_name(d["name"])
        buckets = {}
        cities = set()
        
        # Skanowanie inwestycji (tylko raz na dewelopera)
        dev_path = USI_DATA_DIR / slug
        if dev_path.exists():
            for inv_dir in dev_path.iterdir():
                if not inv_dir.is_dir(): continue
                usi_file = inv_dir / f"usi_{inv_dir.name}.json"
                if usi_file.exists():
                    try:
                        with open(usi_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            coords = data.get("location", {}).get("coords")
                            city = data.get("location", {}).get("city")
                            if city:
                                cities.add(city.strip().lower())
                                
                            specs = data.get("specifications", {})
                            year = specs.get("delivery_year")
                            quarter = specs.get("delivery_quarter")
                            
                            if coords and len(coords) == 2:
                                lat, lon = coords
                                bkey = f"{round(lat, 2):.2f}_{round(lon, 2):.2f}"
                                if bkey not in buckets: buckets[bkey] = []
                                buckets[bkey].append({
                                    "lat": lat, "lon": lon, 
                                    "year": int(year) if year else None,
                                    "quarter": int(quarter) if quarter else None
                                })
                    except Exception: continue

        processed.append({
            "id": d["usi_dev_id"],
            "slug": slug,
            "name": d["name"],
            "norm": norm,
            "buckets": buckets,
            "cities": cities,
            "data": d
        })
    
    # 2. Compare against index
    suggestions_count = 0
    for i, d1 in enumerate(processed):
        suggestions_map = {}
        if not d1["norm"] and not d1["buckets"] and not d1["cities"]: continue
        
        for j, d2 in enumerate(processed):
            if i == j: continue
            best_s = None
            
            city_subset = bool(d1["cities"] and d2["cities"] and (d1["cities"].issubset(d2["cities"]) or d2["cities"].issubset(d1["cities"])))
            
            # A. Name check
            if d1["norm"] and d2["norm"]:
                if d1["norm"] == d2["norm"]:
                    best_s = {"usi_dev_id": d2["id"], "developer_slug": d2["slug"], "reason": "Identyczna znormalizowana nazwa", "score": 1.0}
                elif len(d1["norm"]) > 8 and len(d2["norm"]) > 8:
                    if d1["norm"].startswith(d2["norm"]) or d2["norm"].startswith(d1["norm"]):
                        best_s = {"usi_dev_id": d2["id"], "developer_slug": d2["slug"], "reason": "Nazwa częściowo pokrywa się", "score": 0.85}
                    else:
                        ratio = fuzzy_match(d1["norm"], d2["norm"])
                        if ratio > 0.9:
                            best_s = {"usi_dev_id": d2["id"], "developer_slug": d2["slug"], "reason": "Bardzo podobna nazwa", "score": 0.8}
                        elif ratio > 0.8 and city_subset:
                            best_s = {"usi_dev_id": d2["id"], "developer_slug": d2["slug"], "reason": "Podobna nazwa + te same miasta operacji", "score": 0.78}
            
            # B. Location Bucket Check
            if not best_s and d1["buckets"] and d2["buckets"]:
                pairs_found = 0
                max_depth = 0
                
                for bkey, t_list in d1["buckets"].items():
                    if bkey in d2["buckets"]:
                        o_list = d2["buckets"][bkey]
                        
                        for t_inv in t_list:
                            for o_inv in o_list:
                                # Precise check (3rd/4th decimal)
                                match_depth = 0
                                if round(t_inv["lat"], 3) == round(o_inv["lat"], 3) and round(t_inv["lon"], 3) == round(o_inv["lon"], 3):
                                    match_depth = 3
                                    if round(t_inv["lat"], 4) == round(o_inv["lat"], 4) and round(t_inv["lon"], 4) == round(o_inv["lon"], 4):
                                        match_depth = 4
                                
                                if match_depth >= 3:
                                    time_match = False
                                    if t_inv["year"] and o_inv["year"]:
                                        t_q = t_inv["quarter"] if t_inv["quarter"] else 1
                                        o_q = o_inv["quarter"] if o_inv["quarter"] else 1
                                        q_diff = abs((t_inv["year"] * 4 + t_q) - (o_inv["year"] * 4 + o_q))
                                        if q_diff <= 3:
                                            time_match = True
                                            
                                    name_match = (d1["norm"] and d2["norm"] and fuzzy_match(d1["norm"], d2["norm"]) > 0.5)
                                    
                                    if time_match or name_match:
                                        pairs_found += 1
                                        max_depth = max(max_depth, match_depth)
                                        
                if pairs_found > 0:
                    base_score = 0.75 + (0.05 if max_depth == 4 else 0)
                    score_boost = min(0.1, (pairs_found - 1) * 0.02)
                    final_score = min(0.99, base_score + score_boost)
                    
                    reason = f"Zbieżne inwestycje ({pairs_found} par)"
                    if max_depth == 4: reason += " z b. dużą precyzją geo"
                    
                    best_s = {"usi_dev_id": d2["id"], "developer_slug": d2["slug"], "reason": reason, "score": final_score}

            if best_s:
                # Skip if either side has dismissed the other
                d1_dismissed = dismissed_cache.get(d1["id"], set())
                d2_dismissed = dismissed_cache.get(d2["id"], set())
                if d2["id"] in d1_dismissed or d1["id"] in d2_dismissed:
                    best_s = None

            if best_s:
                suggestions_map[d2["id"]] = best_s

        if suggestions_map:
            d1["data"]["suggestions"] = list(suggestions_map.values())
            dm.create_developer_file(d1["data"])
            suggestions_count += 1

    logger.info(f"Finished. Found suggestions for {suggestions_count} developers.")

if __name__ == "__main__":
    detect_similar()
