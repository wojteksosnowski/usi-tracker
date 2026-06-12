"""
USI Tracker — lokalny interfejs webowy (Wersja produkcyjna — brak crawlerów).
Uruchomienie:  python3 -m python_worker.main ui
"""
import logging
import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify

from python_worker.config import VISIBLE_METADATA_FILE
from python_worker.api.common import get_ui_config, log_ui_error_to_file
from python_worker.api.blueprints.jobs import jobs_bp
from python_worker.api.blueprints.investments import investments_bp
from python_worker.api.blueprints.discovery import discovery_bp
from python_worker.api.blueprints.reports import reports_bp
from python_worker.api.blueprints.poi import poi_bp

logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).parent / "ui"
UI_PORT = int(os.environ.get("USI_PORT", 5000))

app = Flask(__name__, static_folder=None)

# REJESTRACJA BLUEPRINTÓW — crawler_bp został permanentnie usunięty
app.register_blueprint(jobs_bp, url_prefix='/api')
app.register_blueprint(investments_bp, url_prefix='/api')
app.register_blueprint(discovery_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')
app.register_blueprint(poi_bp, url_prefix='/api')

# Czyste, statyczne odpowiedzi informujące frontend o pasywnym stanie systemu
@app.route("/api/system/status", methods=["GET"])
def system_status():
    return jsonify({"status": "ok", "mode": "passive", "daemons": "disabled"})

@app.route("/api/system/verify-library")
def verify_library():
    """Bezpieczna atrapa weryfikacji biblioteki."""
    return jsonify({"ok": True, "version": "0.3.0", "portals": ["rp", "oto", "to"]})

@app.route("/api/config")
def get_config():
    return jsonify(get_ui_config())

@app.route("/api/ui-error", methods=["POST"])
def log_ui_error():
    from flask import request
    payload = request.get_json(silent=True) or {}
    log_ui_error_to_file(payload)
    return jsonify({"ok": True})

@app.route("/api/metadata-config")
def get_metadata_config():
    from flask import send_file
    if VISIBLE_METADATA_FILE.exists():
        return send_file(VISIBLE_METADATA_FILE)
    return jsonify([
        {"key": "address", "label": "Adres", "path": "address", "type": "string"},
        {"key": "segment", "label": "Segment", "path": "specifications.segment", "type": "string"},
        {"key": "units", "label": "Mieszkania", "path": "units", "type": "number"},
        {"key": "delivery", "label": "Termin", "path": "delivery", "type": "string"},
        {"key": "price_avg", "label": "Cena śr.", "path": "price_avg", "type": "currency"},
        {"key": "photos", "label": "Zdjęcia", "path": "photos.length", "type": "count"}
    ])

# ── Static files ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(UI_DIR, filename)

# ── Logging Setup ─────────────────────────────────────────────────────────────

# 1. Bezlitosne wyciszenie domyślnego, śmieciowego loggera Werkzeug
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.WARNING)  # Przepuszcza wyłącznie błędy (4xx/5xx) i ostrzeżenia

# 2. Wdrożenie zwięzłego, biznesowego loggera żądań HTTP
@app.after_request
def log_clean_request(response):
    from flask import request
    
    # Pełna lista endpointów pollingowych i technicznych do całkowitego zignorowania
    ignore_paths = {
        "/api/jobs",
        "/api/crawler/status",
        "/api/doktor/status",
        "/api/system/status",
        "/api/ui-error",
        "/api/reports/pending-summary"  # Dodano brakujące wąskie gardło pollingu
    }
    
    # Ignorujemy również pobieranie plików statycznych (skryptów UI, stylów, ikon)
    if request.path in ignore_paths or request.path.startswith("/assets/") or request.path.endswith(".jsx") or request.path.endswith(".js"):
        return response

    # Logujemy tylko esencję biznesową w jednolitym formacie aplikacji
    logger.info(f"[HTTP] {request.method} {request.path} -> STATUS {response.status_code}")
    return response

@app.route("/assets/icons/<path:filename>")
def serve_or_mock_icon(filename):
    """
    Sprawdza czy ikona istnieje fizycznie na dysku.
    Jeśli tak - serwuje ją. Jeśli nie - zwraca pusty SVG (status 200) zapobiegając błędom 404.
    """
    target_file = UI_DIR / "assets" / "icons" / filename
    if target_file.is_file():
        return send_from_directory(UI_DIR / "assets" / "icons", filename)

    # Bezpieczny fallback dla brakujących ikon
    empty_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"></svg>'
    )
    response = app.response_class(empty_svg, mimetype='image/svg+xml')
    response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    return response

def run():
    print(f"USI Tracker UI (PRODUCTION) → http://localhost:{UI_PORT}")
    app.run(host="127.0.0.1", port=UI_PORT, debug=False, threaded=True, use_reloader=False)

if __name__ == "__main__":
    run()
