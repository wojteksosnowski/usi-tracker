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


def _build_index_entry(raw: dict, file_path: Path, base_path: Path) -> Optional[dict]:
    """
    Buduje wpis indeksu bezpośrednio z raw JSON pliku inwestycji.
    Zero agregacji w locie — tylko przepisanie gotowych pól.
    file_path jest zapisywany jako ścieżka względna od base_path (DROPBOX_PATH).
    """
    usi_inv_id = raw.get("usi_inv_id") or raw.get("usi_id") or raw.get("master_id")
    if not usi_inv_id:
        return None

    loc = raw.get("location", {})
    coords_from_loc = loc.get("coords") or (
        [loc["latitude"], loc["longitude"]]
        if loc.get("latitude") and loc.get("longitude") else None
    )

    try:
        rel_path = str(file_path.relative_to(base_path))
    except ValueError:
        rel_path = str(file_path)

    specs = raw.get("specifications", {})
    financials = raw.get("financials", {})
    amenities_raw = raw.get("amenities", {})
    amenity_labels = (
        amenities_raw.get("labels", []) if isinstance(amenities_raw, dict)
        else amenities_raw if isinstance(amenities_raw, list)
        else []
    )

    # Wylicz source/source_links z sources dict
    sources = raw.get("sources", {})
    source_links = []
    source = raw.get("source", "")
    source_url = raw.get("source_url", "")
    for portal_key, pdata in sources.items():
        if not isinstance(pdata, dict):
            continue
        url = pdata.get("url", "")
        if url:
            source_links.append({"source": portal_key.upper(), "url": url})
            if not source:
                source = portal_key.upper()
                source_url = url

    return {
        "usi_inv_id": usi_inv_id,
        "file_path": rel_path,
        "slug": raw.get("slug", f"{raw.get('developer_slug', '')}/{raw.get('investment_slug', '')}"),
        "developer_slug": raw.get("developer_slug"),
        "investment_slug": raw.get("investment_slug"),
        "name": raw.get("name"),
        "developer": raw.get("developer"),
        "address": raw.get("address") or loc.get("address"),
        "city": raw.get("city") or loc.get("city"),
        "district": raw.get("district") or loc.get("district"),
        "coords": raw.get("coords") or coords_from_loc,
        "source": source,
        "source_url": source_url,
        "source_links": source_links,
        "sources": sources,
        "status": raw.get("status", "Brak"),
        "segment": specs.get("segment") or raw.get("segment"),
        "delivery": specs.get("delivery_date") or raw.get("delivery"),
        "units": specs.get("units_count") or raw.get("units", 0),
        "ceiling_height_min": specs.get("ceiling_height_min"),
        "ceiling_height_max": specs.get("ceiling_height_max"),
        "specifications": specs,
        "price_avg": financials.get("price_avg") or raw.get("price_avg", 0),
        "price_min": financials.get("price_min"),
        "price_max": financials.get("price_max"),
        "price_m2_min": financials.get("price_m2_min"),
        "price_m2_max": financials.get("price_m2_max"),
        "rent_price_min": financials.get("rent_price_min"),
        "rent_price_max": financials.get("rent_price_max"),
        "photos": raw.get("photos", []),
        "images_count": len(raw.get("photos", []) or raw.get("image_paths", [])),
        "amenities": amenity_labels,
        "amenities_score": raw.get("amenities_score", 0),
        "usi_dev_id": raw.get("usi_dev_id"),
        "portal": raw.get("portal"),
        "portal_id": raw.get("portal_id"),
        "master_id": raw.get("master_id"),
        "members": raw.get("members", []),
        "ratings": raw.get("ratings", {}),
        "reviewed": raw.get("reviewed", False),
        "website": raw.get("website"),
        "last_updated_ts": raw.get("last_updated_ts"),
    }


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

            master_id = inv.get("master_id")
            
            # Jeśli to element grupy, podmień status i oceny na te z mastera (single source of truth)
            inv_status = inv.get("status")
            inv_ratings = inv.get("ratings", {})
            if master_id and str(master_id).startswith("IM-"):
                master_inv = self.get_by_id(master_id)
                if master_inv:
                    inv_status = master_inv.get("status", inv_status)
                    inv_ratings = master_inv.get("ratings", inv_ratings)

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
                    "status": inv_status,
                    "master_id": master_id,
                    "ratings": inv_ratings
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
        Skanuje USImaster/ i USIdata/ i buduje indeks.
        Czyta JSON bezpośrednio z dysku — zero agregacji w locie.
        Zapisuje file_path (względna od DROPBOX_PATH) w każdym wpisie.
        """
        with self._rebuild_lock:
            if self._is_rebuilding:
                return 0
            self._is_rebuilding = True

        try:
            logger.info(f"Initial index build: Scanning {self.data_dir} via rglob...")
            start_t = datetime.now()

            from python_worker.config import DROPBOX_PATH
            master_dir = DROPBOX_PATH / "Public" / "USImaster"

            entries = []
            master_member_ids: set = set()

            # 1. Mastery z USImaster/
            if master_dir.exists():
                for mf in master_dir.glob("inv_master_*.json"):
                    try:
                        raw = json.loads(mf.read_text(encoding="utf-8"))
                        master_id = raw.get("master_id") or raw.get("usi_inv_id")
                        if not master_id or not master_id.startswith("IM-"):
                            continue
                        for m in raw.get("members", []):
                            uid = m.get("usi_inv_id") if isinstance(m, dict) else None
                            if uid:
                                master_member_ids.add(uid)
                        entry = _build_index_entry(raw, mf, DROPBOX_PATH)
                        if entry:
                            entries.append(entry)
                    except Exception as e:
                        logger.error(f"Błąd indeksowania mastera {mf}: {e}")

            # 2. USIdata/ — pomijaj members grup
            for usi_file in self.data_dir.rglob("usi_*.json"):
                if "usi_dev_" in usi_file.name:
                    continue
                try:
                    raw = json.loads(usi_file.read_text(encoding="utf-8"))
                    usi_inv_id = raw.get("usi_inv_id") or raw.get("usi_id")
                    if not usi_inv_id or usi_inv_id in master_member_ids:
                        continue
                    # Pomiń members grup (mają master_id)
                    if raw.get("master_id"):
                        continue
                    entry = _build_index_entry(raw, usi_file, DROPBOX_PATH)
                    if entry:
                        entries.append(entry)
                except Exception as e:
                    logger.error(f"Błąd indeksowania {usi_file}: {e}", exc_info=True)

            new_index = {e["usi_inv_id"]: e for e in entries if e.get("usi_inv_id")}
            new_slug_map = {
                f"{e['developer_slug']}/{e['investment_slug']}": e
                for e in entries
                if e.get("developer_slug") and e.get("investment_slug")
            }

            with self._index_lock:
                self._index = new_index
                self._slug_map = new_slug_map
                self._save_to_disk()

            duration = (datetime.now() - start_t).total_seconds()
            logger.info(f"Index rebuilt: {len(entries)} entries in {duration:.2f}s (masters: {sum(1 for e in entries if str(e.get('usi_inv_id','')).startswith('IM-'))})")
            self._notify_change()
            return len(entries)
        finally:
            self._is_rebuilding = False

    def add_or_update(self, usi_id: str, metadata: dict) -> None:
        """
        INCREMENTAL UPDATE O(1) in memory.
        Rekordy z master_id (members grup) są USUWANE z indeksu —
        indeks zawiera tylko samodzielne inwestycje i mastery (IM-XXXX).
        """
        self._load_from_disk()

        with self._index_lock:
            entry = metadata.copy()
            entry["usi_inv_id"] = usi_id
            if not entry.get("investment_slug"):
                entry["investment_slug"] = usi_id
            if not entry.get("folder_path"):
                if usi_id.startswith("IM-"):
                    entry["folder_path"] = "Public/USImaster"
                else:
                    entry["folder_path"] = f"Public/USIdata/{metadata.get('developer_slug', 'unknown')}/{usi_id}"
            entry["updated_at"] = datetime.now().isoformat()
            self._index[usi_id] = entry
            ds = entry.get("developer_slug")
            is_ = entry.get("investment_slug")
            if ds and is_:
                self._slug_map[f"{ds}/{is_}"] = entry
            self._save_to_disk()

        self._notify_change()

    def _save_to_disk(self):
        """Atomic write to _index.json."""
        entries_list = list(self._index.values())
        data = {
            "built_at": datetime.now().isoformat(),
            "count": len(self._index),
            "entries": entries_list,
            # entries_map = szybki O(1) lookup używany przez db.load_investment()
            "entries_map": {e["usi_inv_id"]: e for e in entries_list if e.get("usi_inv_id")},
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
        """Zwraca wszystkie indeksowane inwestycje — mastery zamiast ich memberów."""
        self._load_from_disk()
        return [
            v for v in self._index.values() 
            if not (v.get("master_id") and not str(v.get("usi_inv_id", "")).startswith("IM-"))
        ]

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
    Rejestruje lub aktualizuje pojedynczy rekord w indeksie RAM + dysk.
    Czyta JSON bezpośrednio z dysku.
    """
    from python_worker.config import DROPBOX_PATH
    idx = get_investment_index()

    # Szukaj pliku po ID w istniejącym indeksie
    existing = idx.get_by_id(inv_id)
    
    if inv_id and inv_id.startswith("IM-"):
        file_path = DROPBOX_PATH / "Public" / "USImaster" / f"inv_master_{inv_id}.json"
    elif existing and existing.get("file_path"):
        file_path = DROPBOX_PATH / existing["file_path"]
    elif dev_slug and inv_slug and portal and inv_id:
        file_path = Path(data_dir) / dev_slug / inv_slug / f"usi_{portal}_{inv_id}.json"
    else:
        logger.error(f"Upsert failed: brak danych do lokalizacji pliku dla {inv_id}")
        return False

    if not file_path.exists():
        logger.error(f"Upsert failed: plik nie istnieje: {file_path}")
        return False

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        entry = _build_index_entry(raw, file_path, DROPBOX_PATH)
        if entry:
            idx.add_or_update(inv_id, entry)
            return True
    except Exception as e:
        logger.error(f"Upsert I/O error dla {inv_id}: {e}")
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
