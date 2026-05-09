import json
import logging
import time
from pathlib import Path
from flask import Blueprint, jsonify, abort, request

from python_worker.api.utils import _valid_slug
from python_worker.config import USI_DATA_DIR, HERE_API_KEY

logger = logging.getLogger(__name__)

poi_bp = Blueprint('poi', __name__)

# HERE Places Browse API — category IDs
HERE_CATEGORIES = {
    "food":          "100-1000",
    "entertainment": "200-2000",
    "outdoor":       "300-3000",
    "transport":     "400-4000",
    "shopping":      "600-6000",
    "education":     "700-7000",
    "health":        "800-8000",
}

WIKI_RADIUS_M = 2000
HERE_RADIUS_M = 2000
HERE_LIMIT_PER_CAT = 5


def _poi_path(dev_slug: str, inv_slug: str) -> Path:
    return USI_DATA_DIR / dev_slug / inv_slug / f"poi_{inv_slug}.json"


def _load_inv(dev_slug: str, inv_slug: str) -> dict | None:
    p = USI_DATA_DIR / dev_slug / inv_slug / f"usi_{inv_slug}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch_here_places(lat: float, lon: float) -> list[dict]:
    import urllib.request
    import urllib.parse

    results = []
    seen_ids = set()

    for cat_name, cat_id in HERE_CATEGORIES.items():
        params = urllib.parse.urlencode({
            "at": f"{lat},{lon}",
            "categories": cat_id,
            "limit": HERE_LIMIT_PER_CAT,
            "radius": HERE_RADIUS_M,
            "lang": "pl",
            "apiKey": HERE_API_KEY,
        })
        url = f"https://browse.search.hereapi.com/v1/browse?{params}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                pid = item.get("id", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                cat_label = (item.get("categories") or [{}])[0].get("name", cat_name)
                results.append({
                    "id": pid,
                    "category": cat_name,
                    "category_label": cat_label,
                    "name": item.get("title", ""),
                    "address": item.get("address", {}).get("label", ""),
                    "distance": item.get("distance", 0),
                    "lat": (item.get("position") or {}).get("lat"),
                    "lon": (item.get("position") or {}).get("lng"),
                })
        except Exception as e:
            logger.warning("HERE Places fetch failed for cat %s: %s", cat_name, e)

    results.sort(key=lambda x: x["distance"])
    return results


def _fetch_wiki_articles(lat: float, lon: float) -> list[dict]:
    import urllib.request
    import urllib.parse

    params = urllib.parse.urlencode({
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": WIKI_RADIUS_M,
        "gslimit": 10,
        "format": "json",
        "origin": "*",
    })
    url = f"https://pl.wikipedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "USI-Tracker/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        articles = []
        for item in data.get("query", {}).get("geosearch", []):
            articles.append({
                "title": item.get("title", ""),
                "url": f"https://pl.wikipedia.org/wiki/{item['title'].replace(' ', '_')}",
                "distance": item.get("dist", 0),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
            })
        return sorted(articles, key=lambda x: x["distance"])
    except Exception as e:
        logger.warning("Wikipedia geosearch failed: %s", e)
        return []


@poi_bp.route("/poi/<dev_slug>/<inv_slug>", methods=["GET"])
def get_poi(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    path = _poi_path(dev_slug, inv_slug)
    if not path.exists():
        return jsonify({"status": "missing"}), 404
    try:
        return jsonify(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        abort(500)


@poi_bp.route("/poi/<dev_slug>/<inv_slug>/fetch", methods=["POST"])
def fetch_poi(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)

    inv = _load_inv(dev_slug, inv_slug)
    if not inv:
        return jsonify({"error": "Investment not found"}), 404

    coords = (inv.get("location") or {}).get("coords")
    if coords and len(coords) == 2:
        lat, lon = coords[0], coords[1]
    else:
        lat = inv.get("lat") or inv.get("latitude")
        lon = inv.get("lng") or inv.get("lon") or inv.get("longitude")

    if not lat or not lon:
        return jsonify({"error": "No coordinates for this investment"}), 422

    lat, lon = float(lat), float(lon)

    here_places = _fetch_here_places(lat, lon)
    wiki_articles = _fetch_wiki_articles(lat, lon)

    payload = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lat": lat,
        "lon": lon,
        "here_places": here_places,
        "wiki_articles": wiki_articles,
    }

    path = _poi_path(dev_slug, inv_slug)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return jsonify(payload)
