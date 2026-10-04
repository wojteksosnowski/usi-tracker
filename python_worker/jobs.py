import threading
import time
import logging
import queue
import itertools
from contextlib import contextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_MAX_FINISHED_JOBS = 200
_FINISHED_JOB_TTL_HOURS = 2
_JOB_DELAY_SECONDS = 1.5  # Throttling between starting consecutive jobs
_MAX_JOB_ITEMS = 500
_MAX_JOB_LOG = 200

# Etykiety (PL) statusów pojedynczych elementów raportowanych przez batch pobierania/zapisu
_ITEM_STATUS_LABELS = {
    "started": "pobieranie",
    "retrying": "ponawianie",
    "success": "pobrano",
    "failed": "błąd",
    "saved": "zapisano",
    "save_failed": "błąd zapisu",
}

class JobManager:
    def __init__(self, max_workers=2):
        self.jobs = {}
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.max_workers = max_workers
        self.last_job_start = 0
        self._id_counter = itertools.count(1)
        self._item_pos = {}  # {job_id: {klucz_elementu: pozycja w job["items"]}}

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
                self._item_pos.pop(jid, None)
            
            if len(self.jobs) > _MAX_FINISHED_JOBS:
                evictable = sorted(
                    [j for j in self.jobs.values() if j["status"] not in ("running", "queued")],
                    key=lambda j: j.get("finished_at") or ""
                )
                for job in evictable[:len(self.jobs) - _MAX_FINISHED_JOBS]:
                    del self.jobs[job["id"]]
                    self._item_pos.pop(job["id"], None)

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
                        self.jobs[job_id]["message"] = f"Błąd: {e}"
                        self._append_log(self.jobs[job_id], f"Błąd zadania: {e}", level="error")
                        self.jobs[job_id]["finished_at"] = datetime.now().isoformat()
            finally:
                self.queue.task_done()

    def start_job(self, name, target_func, *args, **kwargs):
        self._prune_old_jobs()
        with self.lock:
            job_id = f"job_{int(time.time())}_{next(self._id_counter)}"
            self.jobs[job_id] = {
                "id": job_id,
                "name": name,
                "status": "queued",
                "progress": 0,
                "total": 100,
                "message": "Waiting in queue...",
                "started_at": datetime.now().isoformat(),
                "finished_at": None,
                "error": None,
                "kind": None,
                "portal": None,
                "phase": None,
                "current": None,
                "counts": {"downloaded": 0, "saved": 0, "failed": 0, "retrying": 0},
                "items": [],
                "log": [],
                "log_seq": 0,
            }
        
        self.queue.put((job_id, target_func, args, kwargs))
        return job_id

    @staticmethod
    def _append_log(job, text, level="info"):
        """Dopisuje linię do ograniczonego bufora logu (wołać pod self.lock)."""
        job["log_seq"] += 1
        job["log"].append({"seq": job["log_seq"], "ts": datetime.now().strftime("%H:%M:%S"), "level": level, "text": text})
        if len(job["log"]) > _MAX_JOB_LOG:
            del job["log"][: len(job["log"]) - _MAX_JOB_LOG]

    def update_progress(self, job_id, progress, message=None, total=None, status=None, phase=None, log=True):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            if progress is not None: job["progress"] = progress
            if message is not None:
                job["message"] = message
                if log:
                    self._append_log(job, message, level="error" if status == "failed" else "info")
            if total is not None: job["total"] = total
            if status is not None:
                job["status"] = status
                if status == "failed" and not job.get("error"):
                    job["error"] = message
            if phase is not None: job["phase"] = phase

    def set_meta(self, job_id, **fields):
        """Ustawia opisowe pola jobu (kind, portal, phase, current)."""
        allowed = {"kind", "portal", "phase", "current"}
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.update({k: v for k, v in fields.items() if k in allowed})

    def record_report(self, job_id, report, scope=None, update_percent=True):
        """
        Przyjmuje raport postępu batcha (format usi_scrapers.process_batch_* oraz zdarzenia saved/save_failed
        z InvestmentSyncService.process_batch) i aktualizuje liczniki, listę elementów, log oraz postęp jobu.
        scope (np. portal) odróżnia elementy o tym samym indeksie z różnych batchy w jednym jobie;
        update_percent=False zostawia pasek postępu wywołującemu.
        """
        if not isinstance(report, dict):
            return
        status = report.get("status")
        index = report.get("current_index")
        inv = report.get("investment") or {}
        ref = inv.get("url") or inv.get("portal_id") or inv.get("ref")
        message = report.get("message")
        error = report.get("error_details")
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            counts = job["counts"]
            if status == "started":
                job["phase"], job["current"] = "fetch", ref
            elif status == "retrying":
                counts["retrying"] += 1
            elif status == "success":
                counts["downloaded"] += 1
                job["phase"] = "save"
            elif status == "saved":
                counts["saved"] += 1
            elif status in ("failed", "save_failed"):
                counts["failed"] += 1

            label = _ITEM_STATUS_LABELS.get(status)
            if label and index is not None:
                pos_map = self._item_pos.setdefault(job_id, {})
                key = (scope, index)
                pos = pos_map.get(key)
                if pos is None and len(job["items"]) < _MAX_JOB_ITEMS:
                    job["items"].append({"index": index, "scope": scope, "ref": ref, "status": status,
                                         "label": label, "message": message, "error": error})
                    pos_map[key] = len(job["items"]) - 1
                elif pos is not None:
                    item = job["items"][pos]
                    item.update({"status": status, "label": label, "message": message, "error": error})
                    item["ref"] = item.get("ref") or ref

            if update_percent and report.get("progress_percent") is not None and status != "started":
                job["progress"] = report["progress_percent"]
            if message:
                text = f"[{scope.upper()}] {message}" if scope else message
                job["message"] = text
                self._append_log(job, text, level="error" if status in ("failed", "save_failed") else "info")

    def log_line(self, job_id, text, current=None):
        """Dopisuje linię do logu jobu (bez zmiany komunikatu/postępu); opcjonalnie ustawia bieżący element."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                if current is not None:
                    job["current"] = current
                self._append_log(job, text)

    @contextmanager
    def track_fetches(self, job_id):
        """Na czas bloku pokazuje w logu jobu każde żądanie wysyłane przez współdzielony Fetcher."""
        try:
            from python_worker.config import get_shared_fetcher
            fetcher = get_shared_fetcher()
        except Exception:
            fetcher = None
        previous = getattr(fetcher, "on_request", None)
        if fetcher is not None:
            fetcher.on_request = lambda url: self.log_line(job_id, f"GET {url}", current=url)
        try:
            yield
        finally:
            if fetcher is not None:
                fetcher.on_request = previous

    @staticmethod
    def _snapshot(job, since=None, light=False):
        out = dict(job)
        out["counts"] = dict(job["counts"])
        if light:
            out.pop("items", None)
            out.pop("log", None)
            out.pop("result", None)  # wynik skanu może być bardzo duży — pobierany przez /jobs/<id>
        else:
            out["items"] = [dict(i) for i in job["items"]]
            out["log"] = [dict(l) for l in job["log"] if since is None or l["seq"] > since]
        return out

    def get_job(self, job_id, since=None):
        with self.lock:
            job = self.jobs.get(job_id)
            return self._snapshot(job, since=since) if job else None

    def list_active_jobs(self):
        with self.lock:
            return [self._snapshot(j, light=True) for j in self.jobs.values() if j["status"] in ("running", "queued")]

    def list_jobs(self):
        """Aktywne i niedawno zakończone (w tym nieudane) joby, najnowsze pierwsze; bez ciężkich pól."""
        with self.lock:
            jobs = [self._snapshot(j, light=True) for j in self.jobs.values()]
        return sorted(jobs, key=lambda j: j.get("started_at") or "", reverse=True)

job_manager = JobManager(max_workers=1)
