import math
import csv
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia']
USI_STATUSES = ['Brak', 'AI', 'Wstępna', 'Poszerzona', 'Pełna', 'Aktualizacja', 'Ukończona']

_WYROZNIKI_CSV = Path(__file__).parent.parent.parent / "data" / "wyrozniki.csv"
_STANDARD_TIERS = [(16, 4), (8, 3), (4, 2), (1, 1), (0, 0)]

@lru_cache(maxsize=1)
def load_wyrozniki():
    w_lok, w_udo = [], []
    if not _WYROZNIKI_CSV.exists():
        return w_lok, w_udo
    try:
        with open(_WYROZNIKI_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lbl = row["Label"]
                rpno = int(row["RPno"]) if row["RPno"] else None
                try:
                    score = int(row["USIudo"])
                except Exception:
                    score = 0
                w_udo.append((lbl, rpno, score))
    except Exception as e:
        logger.error(f"Failed to load wyrozniki: {e}")
    return w_lok, w_udo

def compute_amenity_score(amenity_labels: list, rp_codes: list) -> dict:
    _, wyrozniki_udo = load_wyrozniki()
    matched_lc = {}
    matched_display = {}
    rp_set = set(rp_codes)
    
    for lbl, rpno, hm_udo in wyrozniki_udo:
        lbl_lc = lbl.lower()
        if rpno is not None and rpno in rp_set and lbl_lc not in matched_lc:
            matched_lc[lbl_lc] = hm_udo
            matched_display[lbl_lc] = lbl
            
    for amenity in amenity_labels:
        al = amenity.lower()
        for lbl, _, hm_udo in wyrozniki_udo:
            lbl_lc = lbl.lower()
            if lbl_lc in al and lbl_lc not in matched_lc:
                matched_lc[lbl_lc] = hm_udo
                matched_display[lbl_lc] = lbl
                
    total = sum(matched_lc.values())
    return {
        "score": total,
        "matched": [{"label": matched_display[k], "hm_udo": v} for k, v in matched_lc.items()],
    }

def suggest_udogodnienia(score: int):
    if score <= 0: return None
    for tier, ocena in _STANDARD_TIERS:
        if score > tier: return ocena
    return None

def calculate_ocena_log(ratings: dict) -> float | None:
    vals = [ratings.get(cat) for cat in CATS if ratings.get(cat) is not None]
    if not vals:
        return None
    try:
        sum_exp = sum(math.exp(v) for v in vals)
        return math.log(sum_exp) - math.log(len(vals))
    except (ValueError, OverflowError):
        return None
