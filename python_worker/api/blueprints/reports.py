import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify, abort, request
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.services.investment_loader import load_investment as _load_investment
from python_worker.services.amenity_scorer import calculate_ocena_log as _calculate_ocena_log
from python_worker.api.utils import _calculate_distance
from python_worker.developer_manager import DeveloperManager
from python_worker.services.investment_service import InvestmentService
from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR, HERE_API_KEY
from python_worker.gmaps_url import parse_gmaps_location
from python_worker.services.delivery_filter import matches_delivery, validate_tokens, delivery_years
from python_worker.services.here_maps_service import HereMapsService
import python_worker.investment_index as inv_index
investment_service_facade = InvestmentService(Path(USI_DATA_DIR), Path(PUBLIC_USI_DIR))

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

REPORTS_DIR = Path(USI_DATA_DIR) / "reports"

@reports_bp.route("/reports/pending-summary")
def get_pending_summary():
    """ Centralny endpoint podsumowania raportów.
    
    Zoptymalizowany pod kątem eliminacji narzutu I/O. Wykorzystuje załadowany
    w pamięci RAM indeks deweloperów do wyciągnięcia podstawowych statystyk.
    """
    try:
        from python_worker.developer_indexer import get_shared_developer_index
        dev_index = get_shared_developer_index()
        if dev_index:
            # Pobieramy pre-kalkulowaną listę z pamięci podręcznej indeksu
            all_devs = dev_index.list_developers()
            total_count = len(all_devs)
            
            return jsonify({
                "total_pending": 0,  # Skrobaki są wyłączone, stan zadań oczekujących to synchroniczne 0
                "unregistered_investments": 0,
                "total_tracked_developers": total_count,
                "status": "synchronized"
            })
    except Exception as e:
        logger.error(f"Failed to generate memory-based reports summary: {e}")
        
    # Bezpieczna odpowiedź awaryjna (Graceful Degradation)
    return jsonify({
        "total_pending": 0,
        "unregistered_investments": 0,
        "status": "degraded"
    })

@reports_bp.route("/reports")
def list_reports():
    reports = []
    if not REPORTS_DIR.exists():
        return jsonify([])
    for f in sorted(REPORTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            reports.append({
                "id": data.get("id", f.stem),
                "title": data.get("title", f.stem),
                "description": data.get("description", "")
            })
        except Exception as e:
            logger.error(f"Error reading report {f}: {e}")
    return jsonify(reports)

@reports_bp.route("/report/<report_id>/data")
def get_report_data(report_id):
    report_file = REPORTS_DIR / f"{report_id}.json"
    if not report_file.exists():
        abort(404)
    
    try:
        report_def = json.loads(report_file.read_text(encoding="utf-8"))
        filters = report_def.get("filters", {})
        
        # Używamy zunifikowanej metody z serwisu dla danych raportu
        investments = investment_service_facade.list_investments_filtered(**filters)
        
        return jsonify({
            "definition": report_def,
            "data": investments
        })
    except Exception as e:
        logger.error(f"Error processing report {report_id}: {e}")
        return jsonify({"error": str(e)}), 500


LOCATION_MAX_KM = 50  # bezpiecznik wyszukiwania najbliższych inwestycji


@reports_bp.route("/reports/location", methods=["POST"])
def location_report():
    """`limit` najbliższych inwestycji od lokalizacji (link Map Google / adres / współrzędne).
    Obszar = te inwestycje; area_km = odległość do najdalszej, years = lata oddania w obszarze.
    delivery: lista tokenów zawężających obszar (ready, 2026, 2028+, 2026-Q3, none)."""
    body = request.get_json(silent=True) or {}
    try:
        limit = int(body.get("limit", 12))
    except (TypeError, ValueError):
        return jsonify({"error": "limit musi być liczbą całkowitą"}), 400
    if not 1 <= limit <= 200:
        return jsonify({"error": "limit musi być w przedziale 1..200"}), 400

    tokens = [str(t) for t in (body.get("delivery") or [])]
    try:
        validate_tokens(tokens)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    here = HereMapsService(HERE_API_KEY)
    center = parse_gmaps_location(body.get("location"), geocoder=here.geocode_address)
    if not center:
        return jsonify({"error": "Nie rozpoznano lokalizacji. Wklej link z Map Google, adres lub współrzędne."}), 422

    area = inv_index.get_investment_index().get_near_coordinates(
        center["lat"], center["lon"], LOCATION_MAX_KM, limit=limit)
    years = sorted({y for inv in area for y in delivery_years(inv.get("delivery"))})
    data = [inv for inv in area if matches_delivery(inv.get("delivery"), tokens)]
    return jsonify({"center": center, "limit": limit,
                    "area_km": max((inv["distance"] for inv in area), default=None),
                    "years": years, "total": len(area), "count": len(data), "data": data})
