import json
import logging
import math
from pathlib import Path
from python_worker.config import USI_DEV_DIR, USI_DATA_DIR
from python_worker.developer_manager import DeveloperManager
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def haversine(lat1, lon1, lat2, lon2):
    """Calculates distance between two points on Earth in meters."""
    R = 6371000  # radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_dev_coords(dev_slug: str, data_dir: Path):
    """Collects coordinates for all investments of a developer."""
    coords = []
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
                    if c and isinstance(c, list) and len(c) == 2:
                        coords.append(tuple(c))
    except Exception:
        pass
    return coords

def normalize_name(name: str) -> str:
    """Normalizes developer name for comparison."""
    if not name: return ""
    n = name.lower()
    # Remove dots to simplify legal forms (e.g. S.A. -> sa, Sp. z o.o. -> sp z oo)
    n = n.replace(".", "")
    # Remove common legal forms
    n = re.sub(r"\b(spółka|z oo|sa|spk|sp z oo|sc|sj|spj|holding|group|development|investment|investments|invest|nieruchomości|domy|mieszkania|sp)\b", "", n)
    # Remove remaining punctuation
    n = re.sub(r"[^\w\s]", "", n)
    # Collapse whitespace
    n = " ".join(n.split())
    return n

def detect_similar():
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    devs = dm.list_developers()
    
    logger.info(f"Analyzing {len(devs)} developers for similarities...")
    
    # Pre-normalize all names and collect coordinates
    processed = []
    for d in devs:
        processed.append({
            "id": d["usi_dev_id"],
            "slug": d["developer_slug"],
            "name": d["name"],
            "norm": normalize_name(d["name"]),
            "coords": get_dev_coords(d["developer_slug"], USI_DATA_DIR),
            "data": d
        })
    
    suggestions_count = 0
    
    for i, d1 in enumerate(processed):
        suggestions_map = {}
        if not d1["norm"] and not d1["coords"]: continue
        
        for j, d2 in enumerate(processed):
            if i == j: continue
            
            best_s = None
            
            # 1. Exact normalized name match
            if d1["norm"] and d2["norm"] and d1["norm"] == d2["norm"]:
                best_s = {
                    "usi_dev_id": d2["id"],
                    "developer_slug": d2["slug"],
                    "reason": f"Ten sam znormalizowany nazwa: '{d2['name']}'",
                    "score": 1.0
                }
            # 2. Starts with / Ends with (for very similar names)
            elif (d1["norm"] and d2["norm"] and len(d1["norm"]) > 5 and len(d2["norm"]) > 5) and \
                 (d1["norm"].startswith(d2["norm"]) or d2["norm"].startswith(d1["norm"])):
                 best_s = {
                    "usi_dev_id": d2["id"],
                    "developer_slug": d2["slug"],
                    "reason": f"Nazwa zawiera się w innej: '{d2['name']}'",
                    "score": 0.8
                }
            
            # 3. Location proximity
            if not best_s and d1["coords"] and d2["coords"]:
                for c1 in d1["coords"]:
                    for c2 in d2["coords"]:
                        # Optimization: bounding box check (0.01 deg is ~1.1km)
                        if abs(c1[0] - c2[0]) > 0.01 or abs(c1[1] - c2[1]) > 0.01:
                            continue
                            
                        dist = haversine(c1[0], c1[1], c2[0], c2[1])
                        if dist < 100: # 100 meters
                            best_s = {
                                "usi_dev_id": d2["id"],
                                "developer_slug": d2["slug"],
                                "reason": f"Inwestycje w bardzo bliskiej lokalizacji (<100m)",
                                "score": 0.7
                            }
                            break
                    if best_s: break

            if best_s:
                suggestions_map[d2["id"]] = best_s

        if suggestions_map:
            d1["data"]["suggestions"] = list(suggestions_map.values())
            # Write back to file
            file_path = USI_DEV_DIR / f"usi_dev_{d1['slug']}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(d1["data"], f, indent=2, ensure_ascii=False)
            suggestions_count += 1

    logger.info(f"Finished. Found suggestions for {suggestions_count} developers.")

if __name__ == "__main__":
    detect_similar()
