import json
import logging
import math
import threading
import time
from pathlib import Path
from datetime import datetime, timezone
from python_worker.config import USI_DEV_DIR, USI_DATA_DIR
from python_worker.developer_manager import DeveloperManager
from python_worker.detect_similar_devs import _build_dismissed_cache
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
_TICK_SECONDS = 30  # Slow tick: process one developer every 30s
_INDEX_REFRESH_INTERVAL = 3600 * 4  # Refresh full index every 4 hours

def fuzzy_match(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()

def normalize_name(name: str) -> str:
    if not name: return ""
    n = name.lower()
    n = n.replace(".", "")
    n = re.sub(r"\b(spółka|z oo|sa|spk|sp z oo|sc|sj|spj|holding|group|development|investment|investments|invest|nieruchomości|domy|mieszkania|bud|sp|biuro|zarząd|przedsiebiorstwo|przedsiębiorstwo|budowlane|pphu|phu|pbu|zrb|fhu|firma|uslugowo|usługowo|handlowe|uslugowe|usługowe|handlowa|spoldzielnia|spółdzielnia|mieszkaniowa|immobilier|polska|ograniczona|ograniczoną|odpowiedzialnoscia|odpowiedzialnością)\b", "", n)
    n = re.sub(r"[^\w\s]", "", n)
    n = " ".join(n.split())
    return n

class Doktor:
    """
    The Doktor daemon — a silent, efficient developer similarity investigator.
    It builds a lightweight index of all developers and their investment buckets
    to avoid O(N^2) disk I/O and CPU spikes.
    """
    def __init__(self, data_dir: Path, dev_dir: Path):
        self.data_dir = data_dir
        self.dev_dir = dev_dir
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # In-memory index for fast lookup
        # { "dev_slug": { "id", "name", "norm", "buckets": { "52.22_21.01": [lat, lon, year], ... } } }
        self._index = {}
        self._last_index_refresh = 0
        self._dev_queue = []
        self._dismissed_cache = {}

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="doktor")
        self._thread.start()
        logger.info("Doktor daemon started")

    def stop(self):
        self._stop_event.set()
        logger.info("Doktor stop requested")

    def _run(self):
        # Initial sleep to let the system stabilize
        time.sleep(10)
        
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                logger.error("Doktor tick error: %s", e, exc_info=True)
            self._stop_event.wait(_TICK_SECONDS)

    def _tick(self):
        now = time.time()
        
        # 1. Refresh Index if needed
        if now - self._last_index_refresh > _INDEX_REFRESH_INTERVAL or not self._index:
            self._refresh_index()
            # Reset queue with slugs sorted by something stable (e.g., name)
            self._dev_queue = sorted(list(self._index.keys()))
            self._last_index_refresh = now
            logger.info("Doktor: Index refreshed, processing %d developers in queue", len(self._dev_queue))

        if not self._dev_queue:
            return

        # 2. Pick next developer to investigate
        current_dev_slug = self._dev_queue.pop(0)
        self._investigate(current_dev_slug)

    def _refresh_index(self):
        """Builds a lightweight index of all developers and their investment locations."""
        new_index = {}
        dm = DeveloperManager(self.data_dir, self.dev_dir)
        devs = dm.list_developers()
        
        for d in devs:
            slug = d["developer_slug"]
            norm = normalize_name(d["name"])
            
            buckets = {} # "lat_lon": [ {lat, lon, year, quarter}, ... ]
            cities = set()
            
            # Scan investments for locations
            dev_path = self.data_dir / slug
            if dev_path.exists():
                for inv_dir in dev_path.iterdir():
                    if not inv_dir.is_dir(): continue
                    usi_file = inv_dir / f"usi_{inv_dir.name}.json"
                    if usi_file.exists():
                        try:
                            with open(usi_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                coords = data.get("location", {}).get("coords")
                                city = data.get("location", {}).get("city")
                                if city:
                                    cities.add(city.strip().lower())
                                    
                                specs = data.get("specifications", {})
                                year = specs.get("delivery_year")
                                quarter = specs.get("delivery_quarter")
                                
                                if coords and len(coords) == 2:
                                    lat, lon = coords
                                    # Bucket key at 2 decimal places (~1.1km)
                                    bkey = f"{round(lat, 2):.2f}_{round(lon, 2):.2f}"
                                    if bkey not in buckets: buckets[bkey] = []
                                    buckets[bkey].append({
                                        "lat": lat, "lon": lon, 
                                        "year": int(year) if year else None,
                                        "quarter": int(quarter) if quarter else None
                                    })
                        except Exception:
                            continue
            
            new_index[slug] = {
                "id": d["usi_dev_id"],
                "name": d["name"],
                "norm": norm,
                "buckets": buckets,
                "cities": cities,
                "full_data": d
            }

        self._dismissed_cache = _build_dismissed_cache(self.dev_dir)
        
        with self._lock:
            self._index = new_index

    def _investigate(self, slug: str):
        """Investigates a single developer against the rest of the index."""
        with self._lock:
            if slug not in self._index: return
            target = self._index[slug]
            others = {s: d for s, d in self._index.items() if s != slug}

        suggestions = []
        
        for other_slug, other in others.items():
            best_s = None
            
            city_subset = bool(target["cities"] and other["cities"] and (target["cities"].issubset(other["cities"]) or other["cities"].issubset(target["cities"])))
            
            # 1. Name check (fast)
            if target["norm"] and other["norm"]:
                if target["norm"] == other["norm"]:
                    best_s = {"usi_dev_id": other["id"], "developer_slug": other_slug, 
                              "reason": "Identyczna znormalizowana nazwa", "score": 1.0}
                elif len(target["norm"]) > 8 and len(other["norm"]) > 8:
                    if target["norm"].startswith(other["norm"]) or other["norm"].startswith(target["norm"]):
                        best_s = {"usi_dev_id": other["id"], "developer_slug": other_slug, 
                                  "reason": "Nazwa częściowo pokrywa się", "score": 0.85}
                    else:
                        ratio = fuzzy_match(target["norm"], other["norm"])
                        if ratio > 0.90:
                            best_s = {"usi_dev_id": other["id"], "developer_slug": other_slug, 
                                      "reason": f"Bardzo podobna nazwa ({int(ratio*100)}%)", "score": 0.8}
                        elif ratio > 0.80 and city_subset:
                            best_s = {"usi_dev_id": other["id"], "developer_slug": other_slug, 
                                      "reason": "Podobna nazwa + te same miasta operacji", "score": 0.78}

            # 2. Location Bucket Check
            if not best_s and target["buckets"] and other["buckets"]:
                pairs_found = 0
                max_depth = 0
                
                for bkey, t_list in target["buckets"].items():
                    if bkey in other["buckets"]:
                        o_list = other["buckets"][bkey]
                        
                        for t_inv in t_list:
                            for o_inv in o_list:
                                # Broad hit (1km), now check degree of proximity
                                match_depth = 0
                                if round(t_inv["lat"], 3) == round(o_inv["lat"], 3) and round(t_inv["lon"], 3) == round(o_inv["lon"], 3):
                                    match_depth = 3
                                    if round(t_inv["lat"], 4) == round(o_inv["lat"], 4) and round(t_inv["lon"], 4) == round(o_inv["lon"], 4):
                                        match_depth = 4
                                
                                if match_depth >= 3:
                                    time_match = False
                                    if t_inv["year"] and o_inv["year"]:
                                        t_q = t_inv["quarter"] if t_inv["quarter"] else 1
                                        o_q = o_inv["quarter"] if o_inv["quarter"] else 1
                                        q_diff = abs((t_inv["year"] * 4 + t_q) - (o_inv["year"] * 4 + o_q))
                                        if q_diff <= 3:
                                            time_match = True
                                            
                                    name_match = (target["norm"] and other["norm"] and fuzzy_match(target["norm"], other["norm"]) > 0.5)
                                    
                                    if time_match or name_match:
                                        pairs_found += 1
                                        max_depth = max(max_depth, match_depth)
                                        
                if pairs_found > 0:
                    base_score = 0.75 + (0.05 if max_depth == 4 else 0)
                    score_boost = min(0.1, (pairs_found - 1) * 0.02)
                    final_score = min(0.99, base_score + score_boost)
                    
                    reason = f"Zbieżne inwestycje ({pairs_found} par)"
                    if max_depth == 4: reason += " z b. dużą precyzją geo"
                    
                    best_s = {"usi_dev_id": other["id"], "developer_slug": other_slug, 
                              "reason": reason, "score": final_score}

            if best_s:
                d1_dismissed = self._dismissed_cache.get(target["id"], set())
                d2_dismissed = self._dismissed_cache.get(other["id"], set())
                if other["id"] in d1_dismissed or target["id"] in d2_dismissed:
                    best_s = None

            if best_s:
                suggestions.append(best_s)

        # 3. Save if changed
        current_suggestions = target["full_data"].get("suggestions", [])
        # Simple comparison of IDs to avoid unnecessary writes
        curr_ids = sorted([s["usi_dev_id"] for s in current_suggestions])
        new_ids = sorted([s["usi_dev_id"] for s in suggestions])
        
        if curr_ids != new_ids:
            target["full_data"]["suggestions"] = suggestions
            try:
                dm = DeveloperManager(self.data_dir, self.dev_dir)
                fresh_dev = dm.get_developer(slug)
                if fresh_dev:
                    fresh_dev["suggestions"] = suggestions
                    dm.create_developer_file(fresh_dev)
                    logger.debug("Doktor: Updated suggestions for %s (%d found)", slug, len(suggestions))
            except Exception as e:
                logger.error("Doktor: Failed to save suggestions for %s: %s", slug, e)

    def get_status(self) -> dict:
        running = self._thread is not None and self._thread.is_alive()
        with self._lock:
            total_indexed = len(self._index)
            queue_remaining = len(self._dev_queue)
        last_refresh = None
        if self._last_index_refresh > 0:
            last_refresh = datetime.fromtimestamp(
                self._last_index_refresh, tz=timezone.utc
            ).isoformat()
        return {
            "running": running,
            "total_indexed": total_indexed,
            "queue_remaining": queue_remaining,
            "last_refresh": last_refresh,
            "tick_seconds": _TICK_SECONDS,
            "index_refresh_hours": _INDEX_REFRESH_INTERVAL // 3600,
        }

# ── Singleton ──────────────────────────────────────────────────────────────────
_instance: Doktor | None = None

def init_doktor(data_dir: Path, dev_dir: Path) -> Doktor:
    global _instance
    _instance = Doktor(data_dir, dev_dir)
    return _instance

def get_doktor() -> Doktor:
    return _instance
