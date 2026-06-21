import json
import logging
import threading
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

LAT_BOUND_THRESHOLD = 0.06
LON_BOUND_THRESHOLD = 0.1

class InvestmentIndex:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InvestmentIndex, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, data_dir: Path | str = None, public_usi_dir: Path | str = None):
        if self._initialized:
            return
            
        from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
        self.data_dir = Path(data_dir or USI_DATA_DIR)
        self.public_usi_dir = Path(public_usi_dir or PUBLIC_USI_DIR)
        self.index_path = self.data_dir / "_index.json"
        
        self._index = {} # dict keyed by usi_inv_id
        self._slug_map = {} # dict keyed by dev_slug/inv_slug
        
        self._index_lock = threading.Lock()
        self._rebuild_lock = threading.Lock()
        self._is_rebuilding = False
        self._on_change_callbacks = []
        self._mtime = 0
        
        self.load_or_rebuild()
        self._initialized = True

    def get_near_coordinates(
        self, 
        lat: float, 
        lon: float, 
        max_dist_km: float = 8.0, 
        limit: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje inwestycje w pobliżu wskazanych współrzędnych geograficznych.
        Wykorzystuje dynamiczny Bounding Box i operacje w pamięci podręcznej RAM.
        """
        from python_worker.api.utils import _calculate_distance
        import math

        all_invs = self.get_all()
        nearby = []

        # 1 stopień szerokości geograficznej to w przybliżeniu 111 km
        delta_lat = max_dist_km / 111.0
        
        # Długość stopnia długości geograficznej kurczy się wraz ze zbliżaniem do biegunów
        cos_lat = math.cos(math.radians(lat))
        if cos_lat > 0.01:
            delta_lon = max_dist_km / (111.0 * cos_lat)
        else:
            delta_lon = max_dist_km / 111.0

        for inv in all_invs:
            coords = inv.get("coords")
            if not coords or len(coords) < 2 or coords[0] is None or coords[1] is None:
                continue

            lat2, lon2 = coords[0], coords[1]

            # KROK 1: Błyskawiczne odrzucenie obiektów poza Bounding Boxem (O(1) na obiekt)
            if abs(lat2 - lat) > delta_lat or abs(lon2 - lon) > delta_lon:
                continue

            # KROK 2: Dokładne obliczenie odległości (tylko dla obiektów wewnątrz pudełka)
            dist = _calculate_distance(lat, lon, lat2, lon2)
            if dist <= max_dist_km:
                nearby.append({
                    "usi_inv_id": inv.get("usi_inv_id"),
                    "distance": round(dist, 2),
                    "name": inv.get("name"),
                    "developer": inv.get("developer"),
                    "developer_slug": inv.get("developer_slug"),
                    "investment_slug": inv.get("investment_slug"),
                    "city": inv.get("city"),
                    "coords": coords,
                    "source": inv.get("source"),
                    "status": inv.get("status"),
                    "ratings": inv.get("ratings", {})
                })

        # Sortowanie według dystansu i nałożenie limitu
        nearby.sort(key=lambda x: x["distance"])
        return nearby[:limit]

    def get_nearby_investments(
        self, 
        inv_id: str, 
        coords: List[float], 
        limit: int = 12, 
        max_dist_km: float = 5.0,
        cached_index: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Calculates nearby investments using the global index with a bounding box optimization."""
        from python_worker.api.utils import _calculate_distance
        
        if not coords or not coords[0]: 
            return []

        lat1, lon1 = coords
        all_invs = cached_index if cached_index is not None else self.get_all()
        nearby = []

        for other in all_invs:
            if other.get("usi_inv_id") == inv_id: 
                continue
            
            other_coords = other.get("coords")
            if not other_coords or not other_coords[0]: 
                continue

            lat2, lon2 = other_coords
            if abs(lat2 - lat1) > LAT_BOUND_THRESHOLD or abs(lon2 - lon1) > LON_BOUND_THRESHOLD: 
                continue

            dist = _calculate_distance(lat1, lon1, lat2, lon2)
            if dist <= max_dist_km:
                nearby.append({
                    "usi_inv_id": other.get("usi_inv_id"),
                    "distance": round(dist, 2),
                    "name": other.get("name"),
                    "developer": other.get("developer"),
                    "slug": other.get("slug"),
                    "source": other.get("source"),
                    "ratings": other.get("ratings", {})
                })

        nearby.sort(key=lambda x: x["distance"])
        return nearby[:limit]

    def on_change(self, callback):
        """Register a callback to be called whenever the index is updated or rebuilt."""
        self._on_change_callbacks.append(callback)

    def _notify_change(self):
        """Triggers all registered change callbacks."""
        for cb in self._on_change_callbacks:
            try:
                cb()
            except Exception as e:
                logger.error(f"Error in investment_index change callback: {e}")

    def load_or_rebuild(self) -> None:
        """Loads index from JSON file. If file doesn't exist, builds it once."""
        if self.index_path.exists():
            self._load_from_disk()
        else:
            self.rebuild()

    def _load_from_disk(self):
        with self._index_lock:
            try:
                mtime = self.index_path.stat().st_mtime
                if self._mtime >= mtime:
                    return
                
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                entries = data.get("entries", [])
                
                new_index = {}
                new_slug_map = {}
                for e in entries:
                    inv_id = e.get("usi_inv_id")
                    if inv_id:
                        new_index[inv_id] = e
                        dev_slug = e.get("developer_slug")
                        inv_slug = e.get("investment_slug")
                        if dev_slug and inv_slug:
                            new_slug_map[f"{dev_slug}/{inv_slug}"] = e
                            
                self._index = new_index
                self._slug_map = new_slug_map
                self._mtime = mtime
                logger.info(f"Loaded investment index: {len(self._index)} entries")
            except Exception as e:
                logger.warning(f"Could not read investment index: {e}")

    def rebuild(self) -> int:
        """
        Scans all USIdata subdirectories and builds a unified index file.
        Returns number of entries indexed.
        """
        with self._rebuild_lock:
            if self._is_rebuilding:
                return 0
            self._is_rebuilding = True

        try:
            logger.info(f"Initial index build: Scanning {self.data_dir} via rglob...")
            start_t = datetime.now()
            
            usi_files = list(self.data_dir.rglob("usi_*.json"))
            entries = []
            seen_masters = set()
            # Krok 1: Wczytanie mapowania master_id -> primary_id z plików T3
            master_to_primary = {}
            for master_file in self.data_dir.rglob("inv_master_*.json"):
                try:
                    with open(master_file, "r", encoding="utf-8") as mf:
                        mdata = json.load(mf)
                        mid = mdata.get("master_id")
                        pid = mdata.get("primary_id")
                        if mid and pid:
                            master_to_primary[mid] = pid
                except:
                    pass

            for usi_file in usi_files:
                if "usi_dev_" in usi_file.name: continue
                if usi_file.name.startswith("inv_master_"): continue
                try:
                    data = json.loads(usi_file.read_text())
                    usi_inv_id = data.get("usi_inv_id") or data.get("usi_id")
                    if not usi_inv_id:
                        continue
                        
                    master_id = data.get("master_id")
                    is_grouped = False
                    if master_id:
                        if master_to_primary.get(master_id) != usi_inv_id:
                            is_grouped = True

                    from python_worker.api.utils import _load_investment
                    entry = _load_investment(
                        data_dir=self.data_dir, 
                        public_usi_dir=self.public_usi_dir, 
                        system_id=usi_inv_id, 
                        usi_file=usi_file, 
                        fast_index=True
                    )
                    if entry:
                        entry.pop("image_urls", None)
                        entry.pop("nearby_investments", None)
                        entry["is_grouped"] = is_grouped
                        entries.append(entry)
                except Exception as e:
                    logger.error(f"Krytyczny błąd indeksowania inwestycji z pliku {usi_file}: {e}", exc_info=True)
                    continue

            # Update state
            new_index = {e["usi_inv_id"]: e for e in entries}
            new_slug_map = {f"{e['developer_slug']}/{e['investment_slug']}": e for e in entries if e.get("developer_slug") and e.get("investment_slug")}
            
            with self._index_lock:
                self._index = new_index
                self._slug_map = new_slug_map
                self._save_to_disk()
            
            duration = (datetime.now() - start_t).total_seconds()
            logger.info(f"Index rebuilt: {len(entries)} entries in {duration:.2f}s")
            self._notify_change()
            return len(entries)
        finally:
            self._is_rebuilding = False

    def add_or_update(self, usi_id: str, metadata: dict) -> None:
        """
        INCREMENTAL UPDATE O(1) in memory.
        Jeśli rekord jest secondary (ma master_id ale nie jest primarynym),
        jest USUWANY z indeksu zamiast wstawiany — indeks zawiera tylko primaryne.
        """
        # Ensure latest data is loaded (if changed externally)
        self._load_from_disk()

        with self._index_lock:
            entry = metadata.copy()
            entry["usi_inv_id"] = usi_id
            
            master_id = metadata.get("master_id")
            if master_id:
                # Odszukanie master_file aby sprawdzić primary_id
                # (W trybie hot-reload to rzadkie zjawisko, więc możemy bezpiecznie poszukać)
                master_file = list(self.data_dir.rglob(f"inv_master_{master_id}.json"))
                is_grouped = True
                if master_file:
                    try:
                        with open(master_file[0], "r", encoding="utf-8") as mf:
                            if json.load(mf).get("primary_id") == usi_id:
                                is_grouped = False
                    except: pass
                entry["is_grouped"] = is_grouped
            else:
                entry["is_grouped"] = False
                
            if not entry.get("investment_slug"):
                entry["investment_slug"] = usi_id
            if not entry.get("folder_path"):
                entry["folder_path"] = f"Public/USIdata/{metadata.get('developer_slug', 'unknown')}/{usi_id}"
            entry["updated_at"] = datetime.now().isoformat()

            self._index[usi_id] = entry
            dev_slug = entry.get("developer_slug")
            inv_slug = entry.get("investment_slug")
            if dev_slug and inv_slug:
                self._slug_map[f"{dev_slug}/{inv_slug}"] = entry
            
            self._save_to_disk()
        
        self._notify_change()

    def _save_to_disk(self):
        """Atomic write to _index.json."""
        data = {
            "built_at": datetime.now().isoformat(),
            "count": len(self._index),
            "entries": list(self._index.values()),
            "updated_at": datetime.now().isoformat()
        }
        tmp_path = self.index_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp_path, self.index_path)
            self._mtime = self.index_path.stat().st_mtime
        except Exception as e:
            if tmp_path.exists(): tmp_path.unlink()
            logger.error(f"Failed to persist index to disk: {e}")

    def get_all(self) -> List[Dict]:
        self._load_from_disk()
        return [e for e in self._index.values() if not e.get("is_grouped")]

    def get_by_id(self, inv_id: str) -> Optional[Dict]:
        self._load_from_disk()
        return self._index.get(inv_id)

    def get_by_slug(self, dev_slug: str, inv_slug: str) -> Optional[Dict]:
        self._load_from_disk()
        return self._slug_map.get(f"{dev_slug}/{inv_slug}")

    def invalidate_cache(self):
        """Resets the singleton instance and internal state. Used for testing isolation."""
        with self._lock:
            InvestmentIndex._instance = None
        self._initialized = False
        self._index = {}
        self._slug_map = {}
        self._mtime = 0

# --- Global Singleton and Compatibility Layer ---

def get_investment_index() -> InvestmentIndex:
    return InvestmentIndex()

def invalidate_cache():
    get_investment_index().invalidate_cache()

def get_index(data_dir=None) -> List[Dict]:
    return get_investment_index().get_all()

def load(data_dir=None) -> List[Dict]:
    return get_index(data_dir)

def get_entry_by_id(inv_id: str) -> Optional[Dict]:
    return get_investment_index().get_by_id(inv_id)

def get_entry_by_slug(dev_slug: str, inv_slug: str) -> Optional[Dict]:
    return get_investment_index().get_by_slug(dev_slug, inv_slug)

def add_to_index(data_dir, usi_inv_id, dev_slug, inv_name, portal, portal_id):
    metadata = {
        "developer_slug": dev_slug,
        "name": inv_name,
        "portal": portal,
        "portal_id": portal_id
    }
    get_investment_index().add_or_update(usi_inv_id, metadata)
    return True

def rebuild(data_dir=None, public_usi_dir=None) -> int:
    return get_investment_index().rebuild()

def on_change(callback):
    get_investment_index().on_change(callback)

def upsert(data_dir, public_usi_dir, dev_slug=None, inv_slug=None, portal=None, inv_id=None):
    """
    Safely registers or updates an investment in the memory index.
    Supports fallback path resolution for newly discovered investments.
    """
    idx = get_investment_index()
    from python_worker.api.utils import _load_investment
    from pathlib import Path
    
    # Krok 1: Próba standardowego załadowania po ID (dla istniejących rekordów)
    entry = _load_investment(data_dir=data_dir, public_usi_dir=public_usi_dir, system_id=inv_id, fast_index=True)
    
    # Krok 2: Fallback dla nowo odkrytych inwestycji (brak wpisu w indeksie)
    if not entry and dev_slug and inv_slug and portal and inv_id:
        # Rekonstrukcja ścieżki kanonicznej na podstawie specyfikacji bazy danych
        expected_file = Path(public_usi_dir) / dev_slug / inv_slug / f"usi_{portal}_{inv_id}.json"
        if expected_file.exists():
            entry = _load_investment(
                data_dir=data_dir, 
                public_usi_dir=public_usi_dir, 
                usi_file=expected_file, 
                fast_index=True
            )
            
    if entry:
        entry.pop("image_urls", None)
        entry.pop("nearby_investments", None)
        # Przyrostowa aktualizacja indeksu w pamięci i zrzut atomowy na dysk
        idx.add_or_update(inv_id, entry)
        return True
        
    logger.error(f"Upsert failed: Unable to resolve investment data for ID {inv_id} (Portal: {portal})")
    return False

def remove(data_dir, inv_id):
    idx = get_investment_index()
    with idx._index_lock:
        if inv_id in idx._index:
            entry = idx._index.pop(inv_id)
            ds = entry.get("developer_slug")
            is_ = entry.get("investment_slug")
            if ds and is_:
                idx._slug_map.pop(f"{ds}/{is_}", None)
            idx._save_to_disk()
            idx._notify_change()
            return True
    return False

def get_nearby_investments(inv_id, coords, limit=12, max_dist_km=5.0, cached_index=None):
    return get_investment_index().get_nearby_investments(inv_id, coords, limit, max_dist_km, cached_index)
