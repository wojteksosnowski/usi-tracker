import time
import pytest
from python_worker.jobs import JobManager

def test_job_manager_lifecycle():
    jm = JobManager()
    
    def mock_task(job_id, duration=0.1):
        jm.update_progress(job_id, 50, "Halfway there")
        time.sleep(duration)
        jm.update_progress(job_id, 100, "Done")

    job_id = jm.start_job("Test Job", mock_task, duration=0.2)
    
    # Check initial state
    job = jm.get_job(job_id)
    assert job["status"] == "running"
    assert job["name"] == "Test Job"
    
    # Wait for completion
    time.sleep(0.5)
    
    job = jm.get_job(job_id)
    assert job["status"] == "completed"
    assert job["progress"] == 100
    assert job["message"] == "Finished successfully."

def test_job_manager_failure():
    jm = JobManager()

    def failing_task(job_id):
        raise ValueError("Something went wrong")

    job_id = jm.start_job("Failing Job", failing_task)

    time.sleep(0.2)

    job = jm.get_job(job_id)
    assert job["status"] == "failed"
    assert "Something went wrong" in job["error"]


def test_job_manager_explicit_fail_via_update_progress():
    jm = JobManager()

    def partial_fail_task(job_id):
        jm.update_progress(job_id, 100, "Scraping failed", status="failed")

    job_id = jm.start_job("Partial Fail", partial_fail_task)
    time.sleep(0.2)
    job = jm.get_job(job_id)
    assert job["status"] == "failed"
    assert job["finished_at"] is not None


def test_job_manager_prune_old_jobs():
    from datetime import datetime, timedelta
    jm = JobManager()

    def quick_task(job_id):
        pass

    for _ in range(3):
        jid = jm.start_job("Quick", quick_task)
    time.sleep(0.3)

    # Manually backdate finished_at to simulate old jobs
    for job in jm.jobs.values():
        if job["status"] == "completed":
            job["finished_at"] = (datetime.now() - timedelta(hours=3)).isoformat()

    # Now trigger pruning via a new job
    jm.start_job("Trigger Prune", quick_task)
    time.sleep(0.2)

    remaining_finished = [j for j in jm.jobs.values() if j["status"] == "completed"]
    assert len(remaining_finished) <= 1  # only the trigger job remains (or 0 if also pruned)
