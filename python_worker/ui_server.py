"""
USI Tracker — lokalny interfejs webowy (Modułowy).
Uruchomienie:  python3 -m python_worker.main ui
"""
import logging
import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify

from python_worker.config import USI_DATA_DIR, USI_DEV_DIR, VISIBLE_METADATA_FILE
from python_worker.api.common import get_ui_config, log_ui_error_to_file
from python_worker.api.blueprints.jobs import jobs_bp
from python_worker.api.blueprints.investments import investments_bp
from python_worker.api.blueprints.discovery import discovery_bp
from python_worker.api.blueprints.reports import reports_bp
from python_worker.api.blueprints.poi import poi_bp
from python_worker.api.blueprints.crawler_api import crawler_bp
logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).parent / "ui"
UI_PORT = int(os.environ.get("USI_PORT", 5000))

app = Flask(__name__, static_folder=None)

# Rejestracja Blueprintów
app.register_blueprint(jobs_bp, url_prefix='/api')
app.register_blueprint(investments_bp, url_prefix='/api')
app.register_blueprint(discovery_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')
app.register_blueprint(poi_bp, url_prefix='/api')
app.register_blueprint(crawler_bp, url_prefix='/api')

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

# ── Logging Filter ─────────────────────────────────────────────────────────────

class IgnorePollingFilter(logging.Filter):
    """Filters out frequent polling requests from console output to keep it clean."""
    def filter(self, record):
        msg = record.getMessage()
        return not any(x in msg for x in [
            "GET /api/jobs", 
            "GET /api/crawler/status", 
            "POST /api/ui-error"
        ])

logging.getLogger("werkzeug").addFilter(IgnorePollingFilter())

def run():
    # Start the Doktor daemon (silent similarity investigation)
    # from python_worker.daemons import init_doktor, init_crawler
    # doktor = init_doktor(USI_DATA_DIR, USI_DEV_DIR)
    # if doktor:
    #     doktor.start()

    # crawler = init_crawler(USI_DATA_DIR, USI_DEV_DIR)
    # if crawler:
    #     crawler.start()

    print(f"USI Tracker UI → http://localhost:{UI_PORT}")
    app.run(host="127.0.0.1", port=UI_PORT, debug=False)

if __name__ == "__main__":
    run()
