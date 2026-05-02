import json
import logging
from pathlib import Path
from python_worker.config import USI_DEV_DIR, USI_DATA_DIR
from python_worker.developer_manager import DeveloperManager
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def normalize_name(name: str) -> str:
    """Normalizes developer name for comparison."""
    if not name: return ""
    n = name.lower()
    # Remove common legal forms
    n = re.sub(r"\b(sp\.|spółka|z o\.o\.|z o\.o|sa|s\.a\.|sp\.k\.|sp\. z o\.o\.|sp\. z o\.o|s\.c\.|sj|sp\.j\.|holding|group|development|investments|invest|nieruchomości|domy|mieszkania)\b", "", n)
    # Remove punctuation
    n = re.sub(r"[^\w\s]", "", n)
    # Collapse whitespace
    n = " ".join(n.split())
    return n

def detect_similar():
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    devs = dm.list_developers()
    
    logger.info(f"Analyzing {len(devs)} developers for similarities...")
    
    # Pre-normalize all names
    processed = []
    for d in devs:
        processed.append({
            "id": d["usi_dev_id"],
            "slug": d["developer_slug"],
            "name": d["name"],
            "norm": normalize_name(d["name"]),
            "data": d
        })
    
    suggestions_count = 0
    
    for i, d1 in enumerate(processed):
        suggestions = []
        if not d1["norm"]: continue
        
        for j, d2 in enumerate(processed):
            if i == j: continue
            if not d2["norm"]: continue
            
            # 1. Exact normalized name match
            if d1["norm"] == d2["norm"]:
                suggestions.append({
                    "usi_dev_id": d2["id"],
                    "developer_slug": d2["slug"],
                    "reason": f"Ten sam znormalizowany nazwa: '{d2['name']}'",
                    "score": 1.0
                })
            # 2. Starts with / Ends with (for very similar names)
            elif (len(d1["norm"]) > 5 and len(d2["norm"]) > 5) and (d1["norm"].startswith(d2["norm"]) or d2["norm"].startswith(d1["norm"])):
                 suggestions.append({
                    "usi_dev_id": d2["id"],
                    "developer_slug": d2["slug"],
                    "reason": f"Nazwa zawiera się w innej: '{d2['name']}'",
                    "score": 0.8
                })

        if suggestions:
            d1["data"]["suggestions"] = suggestions
            # Write back to file
            file_path = USI_DEV_DIR / f"usi_dev_{d1['slug']}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(d1["data"], f, indent=2, ensure_ascii=False)
            suggestions_count += 1

    logger.info(f"Finished. Found suggestions for {suggestions_count} developers.")

if __name__ == "__main__":
    detect_similar()
