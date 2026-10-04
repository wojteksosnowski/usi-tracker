from flask import Blueprint, jsonify, abort, request
from python_worker.jobs import job_manager

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route("/jobs")
def list_jobs():
    # ?all=1 → także niedawno zakończone i nieudane (do podglądu na stronie Pobieranie)
    if request.args.get("all"):
        return jsonify(job_manager.list_jobs())
    return jsonify(job_manager.list_active_jobs())

@jobs_bp.route("/jobs/<job_id>")
def get_job_status(job_id):
    since = request.args.get("since", type=int)
    job = job_manager.get_job(job_id, since=since)
    if not job:
        abort(404)
    return jsonify(job)


@jobs_bp.route("/fetcher/status")
def fetcher_status():
    """Stan Fetchera (limity, cooldowny, wyłączniki 403/429) — odczyt z pamięci, bez żądań do portali."""
    from python_worker.config import get_shared_fetcher
    fetcher = get_shared_fetcher()
    if not fetcher or not hasattr(fetcher, "snapshot"):
        return jsonify({"domains": {}, "available": False})
    snap = fetcher.snapshot()
    snap["available"] = True
    return jsonify(snap)
