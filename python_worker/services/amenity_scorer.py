import math
import logging
from python_worker.api.utils import CATS
from python_worker.services.amenity_normalizer import canonicalize, load_catalog

logger = logging.getLogger(__name__)

_STANDARD_TIERS = [(16, 4), (8, 3), (4, 2), (1, 1), (0, 0)]


def compute_amenity_score(amenity_labels: list, rp_codes: list = None, canonical: list = None) -> dict:
    """Wycena udogodnień z katalogu kanonicznego (data/amenity_catalog.json).

    Każde pojęcie liczone raz. `canonical` (lista id) ma pierwszeństwo przed `amenity_labels`.
    `rp_codes` zostaje dla zgodności wywołań (ignorowany).
    """
    cat = load_catalog()
    if canonical is None:
        canonical = canonicalize(amenity_labels or [])["canonical"]
    matched, total = [], 0
    for cid in canonical:
        c = cat["concepts"].get(cid)
        if not c or not c.get("scored", True) or not c.get("points"):
            continue
        total += c["points"]
        matched.append({"code": cid, "label": c["label"], "hm_udo": c["points"]})
    return {"score": total, "matched": matched}

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
