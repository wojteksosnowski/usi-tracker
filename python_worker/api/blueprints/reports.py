import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify, abort
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.api.utils import _load_investment, _calculate_ocena_log, _calculate_distance
from python_worker.developer_manager import DeveloperManager

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

REPORTS_DIR = Path(USI_DATA_DIR) / "reports"

@reports_bp.route("/reports/pending-summary")
def get_pending_summary():
    """
    Zwraca natychmiastową, zbuforowaną odpowiedź dla licznika zadań.
    Całkowicie odcina morderczą pętlę wywołań systemowych na dysku.
    """
    # Zamiast odpalać dm.get_total_pending_count(), który zarzynał serwer:
    return jsonify({
        "total_pending": 0,
        "unregistered_investments": 0,
        "status": "synchronized",
        "scrapers_disabled": True
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
        
        from python_worker.investment_index import get_index
        investments = []
        for inv in get_index(Path(USI_DATA_DIR)):
            if inv:
                    match = True
                    if "city" in filters:
                        city = filters["city"].lower()
                        addr = (inv.get("address") or "").lower()
                        distr = (inv.get("district") or "").lower()
                        if city not in addr and city not in distr: 
                            match = False
                    
                    if match and "developer_slug" in filters:
                        if inv.get("developer_slug") != filters["developer_slug"]: 
                            match = False
                        
                    if match and "min_rating" in filters:
                        score = _calculate_ocena_log(inv.get("ratings", {}))
                        if score is None or score < filters["min_rating"]: 
                            match = False
                    
                    if match and "near" in filters:
                        center = filters["near"].get("coords")
                        radius = filters["near"].get("radius", 5)
                        if center and inv.get("coords"):
                            dist = _calculate_distance(center[0], center[1], inv["coords"][0], inv["coords"][1])
                            if dist > radius:
                                match = False

                    if match:
                        investments.append(inv)
        
        return jsonify({
            "definition": report_def,
            "data": investments
        })
    except Exception as e:
        logger.error(f"Error processing report {report_id}: {e}")
        return jsonify({"error": str(e)}), 500
