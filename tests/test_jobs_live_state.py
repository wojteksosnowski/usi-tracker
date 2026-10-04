import time

from python_worker.jobs import JobManager


def _wait(jm, job_id, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        job = jm.get_job(job_id)
        if job and job["status"] not in ("queued", "running"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_record_report_tracks_items_counts_and_log():
    jm = JobManager(max_workers=1)

    def work(job_id):
        jm.record_report(job_id, {"status": "started", "current_index": 1, "total": 2, "progress_percent": 0,
                                  "investment": {"url": "http://a"}, "message": "Pobieram: http://a"})
        jm.record_report(job_id, {"status": "success", "current_index": 1, "total": 2, "progress_percent": 50,
                                  "investment": {"url": "http://a"}, "message": "Pobrano pomyślnie."})
        jm.record_report(job_id, {"status": "saved", "current_index": 1, "total": 2, "progress_percent": 50,
                                  "investment": {"ref": "http://a"}, "message": "Zapisano rp_1"})
        jm.record_report(job_id, {"status": "failed", "current_index": 2, "total": 2, "progress_percent": 100,
                                  "investment": {"url": "http://b"}, "message": "Pobranie nieudane: x",
                                  "error_details": "x"})

    job = _wait(jm, jm.start_job("t", work))
    assert job["counts"] == {"downloaded": 1, "saved": 1, "failed": 1, "retrying": 0}
    items = {i["index"]: i for i in job["items"]}
    assert items[1]["status"] == "saved" and items[1]["ref"] == "http://a"
    assert items[2]["status"] == "failed" and items[2]["error"] == "x"
    assert [l["seq"] for l in job["log"]] == sorted(l["seq"] for l in job["log"])
    assert any("Zapisano rp_1" in l["text"] for l in job["log"])

    later = jm.get_job(job["id"], since=job["log"][-2]["seq"])
    assert len(later["log"]) == 1


def test_failed_job_is_listed_with_error_and_ids_are_unique():
    jm = JobManager(max_workers=1)

    def boom(job_id):
        raise RuntimeError("kaput")

    ids = {jm.start_job(f"j{i}", boom) for i in range(5)}
    assert len(ids) == 5
    for jid in ids:
        _wait(jm, jid)
    listed = jm.list_jobs()
    assert all(j["status"] == "failed" and "kaput" in j["error"] for j in listed)
    assert all("items" not in j and "log" not in j for j in listed)
    assert jm.list_active_jobs() == []


def test_update_progress_failed_sets_error():
    jm = JobManager(max_workers=1)

    def work(job_id):
        jm.update_progress(job_id, 100, "źle", status="failed")

    job = _wait(jm, jm.start_job("t", work))
    assert job["status"] == "failed" and job["error"] == "źle" and job["finished_at"]


def test_track_fetches_logs_requests_and_restores_hook():
    from unittest.mock import MagicMock, patch
    jm = JobManager(max_workers=1)
    fetcher = MagicMock()
    fetcher.on_request = "orig"

    def work(job_id):
        with patch("python_worker.config.get_shared_fetcher", return_value=fetcher):
            with jm.track_fetches(job_id):
                fetcher.on_request("https://x/y")
        assert fetcher.on_request == "orig"

    job = _wait(jm, jm.start_job("t", work))
    assert job["status"] == "completed"
    assert any(l["text"] == "GET https://x/y" for l in job["log"])
    assert job["current"] == "https://x/y"


def test_register_bulk_endpoint_exposes_live_state():
    from unittest.mock import MagicMock, patch
    from python_worker.ui_server import app

    sync = MagicMock()

    def fake_batch(portal, invs, on_progress_callback=None):
        for i in range(2):
            on_progress_callback({"status": "started", "current_index": i + 1, "total": 2, "progress_percent": 50 * i,
                                  "investment": {"url": f"http://x/{i}"}, "message": f"Pobieram: http://x/{i}"})
            on_progress_callback({"status": "success", "current_index": i + 1, "total": 2, "progress_percent": 50 * (i + 1),
                                  "investment": {"url": f"http://x/{i}"}, "message": "Pobrano pomyślnie."})
            if i == 0:
                on_progress_callback({"status": "saved", "current_index": 1, "total": 2, "progress_percent": 50,
                                      "investment": {"ref": "http://x/0"}, "message": "Zapisano rp_1"})
            else:
                on_progress_callback({"status": "save_failed", "current_index": 2, "total": 2, "progress_percent": 100,
                                      "investment": {"ref": "http://x/1"}, "message": "Zapis nieudany: x", "error_details": "x"})
        return 1

    sync.process_batch.side_effect = fake_batch
    client = app.test_client()
    with patch("python_worker.api.blueprints.investments._get_sync", return_value=sync):
        resp = client.post("/api/register-bulk", json={"portal": "rp", "investments": [{"url": "http://x/0"}, {"url": "http://x/1"}]})
        job_id = resp.get_json()["job_id"]
        job = None
        for _ in range(100):
            job = client.get(f"/api/jobs/{job_id}").get_json()
            if job["status"] not in ("queued", "running"):
                break
            time.sleep(0.1)

    assert job["status"] == "completed"
    assert job["counts"]["saved"] == 1 and job["counts"]["failed"] == 1 and job["counts"]["downloaded"] == 2
    assert {i["ref"]: i["status"] for i in job["items"]} == {"http://x/0": "saved", "http://x/1": "save_failed"}
    assert job["kind"] == "download" and job["portal"] == "rp"
    listed = [j for j in client.get("/api/jobs?all=1").get_json() if j["id"] == job_id]
    assert listed and "log" not in listed[0]
