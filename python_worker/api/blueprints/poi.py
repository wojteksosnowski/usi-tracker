import json
import logging
import time
from pathlib import Path
from flask import Blueprint, jsonify, abort, request

from python_worker.config import HERE_API_KEY
from python_worker.services.here_maps_service import HereMapsService

logger = logging.getLogger(__name__)

poi_bp = Blueprint('poi', __name__)

WIKI_RADIUS_M = 2000

def _poi_path(system_id: str) -> Path | None:
    from python_worker.api.blueprints.investments import investment_service
    resources = investment_service.get_investment_resources(system_id)
    if not resources or not resources.get("base_dir"):
        return None
    return resources["base_dir"] / "poi.json"

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


@poi_bp.route("/poi/<system_id>", methods=["GET"])
def get_poi(system_id):
    if not system_id:
        abort(400)
        
    from python_worker.api.blueprints.investments import investment_service
    inv_data = investment_service.repo.get_investment_json(system_id)
    if not inv_data:
        abort(404)
        
    if "poi" in inv_data:
        return jsonify(inv_data["poi"])

    path = _poi_path(system_id)
    if not path or not path.exists():
        # Fallback for old name poi_{inv_slug}.json
        inv = investment_service.get_investment(system_id)
        if inv and inv.get("investment_slug"):
            res = investment_service.get_investment_resources(system_id)
            if res and res.get("base_dir"):
                 legacy_path = res["base_dir"] / f"poi_{inv['investment_slug']}.json"
                 if legacy_path.exists():
                     path = legacy_path

    if not path or not path.exists():
        return jsonify({"status": "missing"}), 404
    try:
        return jsonify(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        abort(500)


@poi_bp.route("/poi/<system_id>/fetch", methods=["POST"])
def fetch_poi(system_id):
    if not system_id:
        abort(400)

    from python_worker.api.blueprints.investments import investment_service
    inv = investment_service.get_investment(system_id)
    if not inv:
        return jsonify({"error": "Investment not found"}), 404

    coords = inv.get("coords")
    if coords and len(coords) == 2:
        lat, lon = coords[0], coords[1]
    else:
        lat, lon = None, None

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

    inv_data = investment_service.repo.get_investment_json(system_id)
    if not inv_data:
        abort(500)
        
    inv_data["poi"] = payload
    investment_service.repo.save_investment_json(system_id, inv_data)

    return jsonify(payload)
