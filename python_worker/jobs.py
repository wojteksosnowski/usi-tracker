import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start_job(self, name, target_func, *args, **kwargs):
        job_id = f"job_{int(time.time())}_{len(self.jobs)}"
        self.jobs[job_id] = {
            "id": job_id,
            "name": name,
            "status": "running",
            "progress": 0,
            "total": 100,
            "message": "Initializing...",
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "error": None
        }
        
        def wrapper():
            try:
                target_func(job_id, *args, **kwargs)
                with self.lock:
                    self.jobs[job_id]["status"] = "completed"
                    self.jobs[job_id]["progress"] = self.jobs[job_id]["total"]
                    self.jobs[job_id]["message"] = "Finished successfully."
                    self.jobs[job_id]["finished_at"] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                with self.lock:
                    self.jobs[job_id]["status"] = "failed"
                    self.jobs[job_id]["error"] = str(e)
                    self.jobs[job_id]["finished_at"] = datetime.now().isoformat()

        threading.Thread(target=wrapper, daemon=True).start()
        return job_id

    def update_progress(self, job_id, progress, message=None, total=None):
        with self.lock:
            if job_id in self.jobs:
                if progress is not None: self.jobs[job_id]["progress"] = progress
                if message is not None: self.jobs[job_id]["message"] = message
                if total is not None: self.jobs[job_id]["total"] = total

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def list_active_jobs(self):
        return [j for j in self.jobs.values() if j["status"] == "running"]

job_manager = JobManager()
