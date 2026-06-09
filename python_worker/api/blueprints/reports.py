import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify, abort
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.services.investment_loader import load_investment as _load_investment
from python_worker.services.amenity_scorer import calculate_ocena_log as _calculate_ocena_log
from python_worker.api.utils import _calculate_distance, filter_investments
from python_worker.developer_manager import DeveloperManager

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
        
        from python_worker.investment_index import get_index
        all_investments = get_index(Path(USI_DATA_DIR))
        
        # Używamy uniwersalnego filtru dla danych raportu
        investments = filter_investments(all_investments, filters)
        
        return jsonify({
            "definition": report_def,
            "data": investments
        })
    except Exception as e:
        logger.error(f"Error processing report {report_id}: {e}")
        return jsonify({"error": str(e)}), 500
