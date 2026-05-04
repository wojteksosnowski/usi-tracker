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
