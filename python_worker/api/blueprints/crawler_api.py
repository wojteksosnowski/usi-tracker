import logging
from flask import Blueprint, jsonify, abort, request
from python_worker.api.utils import _valid_slug

logger = logging.getLogger(__name__)

crawler_bp = Blueprint('crawler', __name__)


def _get_crawler():
    from python_worker.crawler import get_crawler
    return get_crawler()


@crawler_bp.route("/crawler/status", methods=["GET"])
def crawler_status():
    c = _get_crawler()
    if not c:
        return jsonify({"running": False, "paused": False})
    return jsonify(c.get_status())


@crawler_bp.route("/crawler/pause", methods=["POST"])
def crawler_pause():
    c = _get_crawler()
    if c:
        c.pause()
    return jsonify({"ok": True})


@crawler_bp.route("/crawler/resume", methods=["POST"])
def crawler_resume():
    c = _get_crawler()
    if c:
        c.resume()
    return jsonify({"ok": True})


@crawler_bp.route("/crawler/badge-reset/<dev_slug>", methods=["POST"])
def badge_reset(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    usi_dev_id = request.args.get("id")
    if usi_dev_id:
        from python_worker.developer_manager import DeveloperManager
        from python_worker.config import USI_DATA_DIR
        from pathlib import Path
        dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
        dev = dm.get_developer_by_id(usi_dev_id)
        if dev:
            dev_slug = dev["developer_slug"]
    c = _get_crawler()
    if c:
        c.reset_badge(dev_slug)
    return jsonify({"ok": True})


@crawler_bp.route("/crawler/exploration", methods=["GET"])
def crawler_exploration():
    c = _get_crawler()
    if not c:
        return jsonify({})
    return jsonify(c.get_exploration_status())


@crawler_bp.route("/doktor/status", methods=["GET"])
def doktor_status():
    from python_worker.doktor import get_doktor
    d = get_doktor()
    if not d:
        return jsonify({"running": False})
    return jsonify(d.get_status())
