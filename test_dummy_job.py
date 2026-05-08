import time
from python_worker.jobs import job_manager

def dummy_task(job_id, duration=10):
    for i in range(duration):
        time.sleep(1)
        job_manager.update_progress(job_id, (i + 1) * (100 // duration), f"Step {i+1} of {duration}")
    print("Dummy task finished")

if __name__ == "__main__":
    job_id = job_manager.start_job("Dummy Job", dummy_task, duration=20)
    print(f"Started dummy job: {job_id}")
    while True:
        job = job_manager.get_job(job_id)
        if job["status"] in ["completed", "failed"]:
            print(f"Job finished with status: {job['status']}")
            break
        print(f"Progress: {job['progress']}% - {job['message']}")
        time.sleep(2)
