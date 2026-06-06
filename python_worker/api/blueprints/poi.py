import json
import logging
import time
import concurrent.futures
import urllib.request
import urllib.parse
from pathlib import Path
from flask import Blueprint, jsonify, abort

from python_worker.config import HERE_API_KEY
from python_worker.services.here_maps_service import HereMapsService

logger = logging.getLogger(__name__)
poi_bp = Blueprint('poi', __name__)

WIKI_RADIUS_M = 2000

# Reużywalna pula wątków na poziomie modułu — zapobiega overheadowi tworzenia puli per-request
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
here_svc = HereMapsService(HERE_API_KEY)


def _get_investment_service():
    """Opóźniony pobór serwisu w celu uniknięcia cyklicznego importu."""
    from python_worker.api.blueprints.investments import investment_service
    return investment_service


def _poi_path(system_id: str) -> Path | None:
    inv_svc = _get_investment_service()
    resources = inv_svc.get_investment_resources(system_id)
    if not resources or not resources.get("base_dir"):
        return None
    return resources["base_dir"] / "poi.json"


def _fetch_wiki_articles(lat: float, lon: float) -> list[dict]:
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

    inv_svc = _get_investment_service()
    inv_data = inv_svc.repo.get_investment_json(system_id)
    if not inv_data:
        abort(404)

    if "poi" in inv_data:
        return jsonify(inv_data["poi"])

    path = _poi_path(system_id)
    if not path or not path.exists():
        inv = inv_svc.get_investment(system_id)
        if inv and inv.get("investment_slug"):
            res = inv_svc.get_investment_resources(system_id)
            if res and res.get("base_dir"):
                legacy_path = res["base_dir"] / f"poi_{inv['investment_slug']}.json"
                if legacy_path.exists():
                    path = legacy_path

    if not path or not path.exists():
        return jsonify({"status": "missing"}), 404

    try:
        return jsonify(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        logger.exception("Failed to read POI file for system_id %s", system_id)
        abort(500)


@poi_bp.route("/poi/<system_id>/fetch", methods=["POST"])
def fetch_poi(system_id):
    if not system_id:
        abort(400)

    inv_svc = _get_investment_service()
    inv = inv_svc.get_investment(system_id)
    if not inv:
        return jsonify({"error": "Investment not found"}), 404

    coords = inv.get("coords")
    if not coords or len(coords) != 2:
        return jsonify({"error": "No coordinates for this investment"}), 422

    try:
        lat, lon = float(coords[0]), float(coords[1])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid coordinates format"}), 422

    # Równoległe zapytania HERE + Wikipedia z reużywalnej puli modułu
    future_here = executor.submit(here_svc.fetch_places, lat, lon)
    future_wiki = executor.submit(_fetch_wiki_articles, lat, lon)

    here_places = future_here.result()
    wiki_articles = future_wiki.result()

    payload = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lat": lat,
        "lon": lon,
        "here_places": here_places,
        "wiki_articles": wiki_articles,
    }

    inv_data = inv_svc.repo.get_investment_json(system_id)
    if not inv_data:
        logger.error("Investment base JSON missing during POI save for ID %s", system_id)
        abort(500)

    inv_data["poi"] = payload
    inv_svc.repo.save_investment_json(system_id, inv_data)

    return jsonify(payload)
