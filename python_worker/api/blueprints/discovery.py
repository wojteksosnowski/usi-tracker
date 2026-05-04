import logging
from flask import Blueprint, jsonify, request
from python_worker.services.discovery_service import DiscoveryService
from python_worker.jobs import job_manager

logger = logging.getLogger(__name__)

discovery_bp = Blueprint('discovery', __name__)
discovery_service = DiscoveryService()

@discovery_bp.route("/developer/<dev_slug>/discover", methods=["POST"])
def discover_dev_new(dev_slug):
    job_id = job_manager.start_job(
        f"Discovery: {dev_slug}", 
        discovery_service.discover_for_developer, 
        dev_slug, 
        job_manager=job_manager
    )
    return jsonify({"ok": True, "job_id": job_id})

@discovery_bp.route("/discovery/<portal>")
def discovery(portal):
    identifier = request.args.get("id", "").strip()
    try:
        results = discovery_service.discovery_by_portal(portal, identifier)
        return jsonify(results)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Discovery error for {portal}: {e}")
        return jsonify({"error": str(e)}), 500
