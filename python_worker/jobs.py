import threading
import time
import logging
import queue
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_MAX_FINISHED_JOBS = 200
_FINISHED_JOB_TTL_HOURS = 2
_JOB_DELAY_SECONDS = 1.5  # Throttling between starting consecutive jobs

class JobManager:
    def __init__(self, max_workers=2):
        self.jobs = {}
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.max_workers = max_workers
        self.last_job_start = 0
        
        # Start worker threads
        for i in range(self.max_workers):
            t = threading.Thread(target=self._worker, name=f"JobWorker-{i}", daemon=True)
            t.start()

    def _prune_old_jobs(self):
        with self.lock:
            cutoff = (datetime.now() - timedelta(hours=_FINISHED_JOB_TTL_HOURS)).isoformat()
            finished_ids = [
                jid for jid, j in self.jobs.items()
                if j["status"] not in ("running", "queued") and (j.get("finished_at") or "") < cutoff
            ]
            for jid in finished_ids:
                del self.jobs[jid]
            
            if len(self.jobs) > _MAX_FINISHED_JOBS:
                evictable = sorted(
                    [j for j in self.jobs.values() if j["status"] not in ("running", "queued")],
                    key=lambda j: j.get("finished_at") or ""
                )
                for job in evictable[:len(self.jobs) - _MAX_FINISHED_JOBS]:
                    del self.jobs[job["id"]]

    def _worker(self):
        while True:
            job_id, target_func, args, kwargs = self.queue.get()
            try:
                # Throttling: ensure minimum delay between starting jobs
                with self.lock:
                    now = time.time()
                    wait_time = max(0, self.last_job_start + _JOB_DELAY_SECONDS - now)
                    self.last_job_start = now + wait_time
                
                if wait_time > 0:
                    time.sleep(wait_time)

                with self.lock:
                    if job_id in self.jobs:
                        self.jobs[job_id]["status"] = "running"
                        self.jobs[job_id]["message"] = "Processing..."

                logger.info(f"Starting job {job_id} ({self.jobs[job_id]['name']})")
                result = target_func(job_id, *args, **kwargs)
                
                with self.lock:
                    if job_id in self.jobs:
                        self.jobs[job_id]["result"] = result
                        if self.jobs[job_id]["status"] == "running":
                            self.jobs[job_id]["status"] = "completed"
                            self.jobs[job_id]["progress"] = self.jobs[job_id]["total"]
                            self.jobs[job_id]["message"] = "Finished successfully."
                            self.jobs[job_id]["finished_at"] = datetime.now().isoformat()
                        elif not self.jobs[job_id]["finished_at"]:
                            self.jobs[job_id]["finished_at"] = datetime.now().isoformat()
            except Exception as e:
                logger.exception(f"Job {job_id} failed: {e}")
                with self.lock:
                    if job_id in self.jobs:
                        self.jobs[job_id]["status"] = "failed"
                        self.jobs[job_id]["error"] = str(e)
                        self.jobs[job_id]["finished_at"] = datetime.now().isoformat()
            finally:
                self.queue.task_done()

    def start_job(self, name, target_func, *args, **kwargs):
        self._prune_old_jobs()
        with self.lock:
            job_id = f"job_{int(time.time())}_{len(self.jobs)}"
            self.jobs[job_id] = {
                "id": job_id,
                "name": name,
                "status": "queued",
                "progress": 0,
                "total": 100,
                "message": "Waiting in queue...",
                "started_at": datetime.now().isoformat(),
                "finished_at": None,
                "error": None
            }
        
        self.queue.put((job_id, target_func, args, kwargs))
        return job_id

    def update_progress(self, job_id, progress, message=None, total=None, status=None):
        with self.lock:
            if job_id in self.jobs:
                if progress is not None: self.jobs[job_id]["progress"] = progress
                if message is not None: self.jobs[job_id]["message"] = message
                if total is not None: self.jobs[job_id]["total"] = total
                if status is not None: self.jobs[job_id]["status"] = status

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def list_active_jobs(self):
        return [j for j in self.jobs.values() if j["status"] in ("running", "queued")]

job_manager = JobManager(max_workers=2)
