import json
import logging
import time
from pathlib import Path
from flask import Blueprint, jsonify, abort, request

from python_worker.api.utils import _valid_slug
from python_worker.config import USI_DATA_DIR, HERE_API_KEY
from python_worker.services.here_maps_service import HereMapsService

logger = logging.getLogger(__name__)

poi_bp = Blueprint('poi', __name__)

WIKI_RADIUS_M = 2000

def _poi_path(dev_slug: str, inv_slug: str) -> Path:
    return USI_DATA_DIR / dev_slug / inv_slug / f"poi_{inv_slug}.json"


def _load_inv(dev_slug: str, inv_slug: str) -> dict | None:
    from python_worker.api.utils import _find_inv_file
    inv_dir = USI_DATA_DIR / dev_slug / inv_slug
    p = _find_inv_file(inv_dir, inv_slug)
    if not p or not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


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
        
    system_id = request.args.get("id")
    if system_id:
        from python_worker.api.blueprints.investments import investment_service
        inv = investment_service.get_investment(system_id)
        if inv:
            dev_slug = inv.get("developer_slug", dev_slug)
            inv_slug = inv.get("investment_slug", inv_slug)
            
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

    system_id = request.args.get("id")
    if system_id:
        from python_worker.api.blueprints.investments import investment_service
        inv = investment_service.get_investment(system_id)
        if inv:
            dev_slug = inv.get("developer_slug", dev_slug)
            inv_slug = inv.get("investment_slug", inv_slug)
    else:
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

    here_svc = HereMapsService(HERE_API_KEY)
    here_places = here_svc.fetch_places(lat, lon)
    wiki_articles = _fetch_wiki_articles(lat, lon)

    payload = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lat": lat,
        "lon": lon,
        "here_places": here_places,
        "wiki_articles": wiki_articles,
    }

    path = _poi_path(dev_slug, inv_slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return jsonify(payload)
