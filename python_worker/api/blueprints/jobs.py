from flask import Blueprint, jsonify, abort
from python_worker.jobs import job_manager

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route("/jobs")
def list_jobs():
    return jsonify(job_manager.list_active_jobs())

@jobs_bp.route("/jobs/<job_id>")
def get_job_status(job_id):
    job = job_manager.get_job(job_id)
    if not job:
        abort(404)
    return jsonify(job)
