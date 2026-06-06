import json
import logging
import threading
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_index_cache = None
_index_cache_mtime = 0
_index_lock = threading.Lock()
_rebuild_lock = threading.Lock()
_is_rebuilding = False
_on_change_callbacks = []

def on_change(callback):
    """Register a callback to be called whenever the index is updated or rebuilt."""
    _on_change_callbacks.append(callback)

def _notify_change():
    """Triggers all registered change callbacks."""
    for cb in _on_change_callbacks:
        try:
            cb()
        except Exception as e:
            logger.error(f"Error in investment_index change callback: {e}")

# Mapping: 
# "slugs" -> { "dev_slug/inv_slug": entry }
# "ids" -> { "usi_inv_id": entry }
_hot_index = {"slugs": {}, "ids": {}}

def _update_hot_index(entries: list):
    global _hot_index
    new_slugs = {}
    new_ids = {}
    for e in entries:
        dev_slug = e.get("developer_slug")
        inv_slug = e.get("investment_slug")
        inv_id = e.get("usi_inv_id")
        if dev_slug and inv_slug:
            new_slugs[f"{dev_slug}/{inv_slug}"] = e
        if inv_id:
            new_ids[inv_id] = e
    _hot_index = {"slugs": new_slugs, "ids": new_ids}

def _index_path(data_dir: Path | str) -> Path:
    from pathlib import Path
    return Path(data_dir) / "_index.json"

def _atomic_write_json(path: Path, data: dict):
    """Writes JSON to a temporary file and replaces the target file atomically."""
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, path)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise e

def get_entry_by_slug(dev_slug: str, inv_slug: str) -> Optional[dict]:
    return _hot_index["slugs"].get(f"{dev_slug}/{inv_slug}")

def get_entry_by_id(inv_id: str) -> Optional[dict]:
    return _hot_index["ids"].get(inv_id)

def get_index(data_dir: Path) -> list:
    """Returns the list of indexed investments, cached in memory."""
    global _index_cache, _index_cache_mtime
    import time
    start_t = time.time()
    path = _index_path(data_dir)
    if not path.exists():
        return []
    
    with _index_lock:
        try:
            mtime = path.stat().st_mtime
            if _index_cache is not None and mtime <= _index_cache_mtime:
                return _index_cache
                
            read_start = time.time()
            raw_text = path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            _index_cache = data.get("entries", [])
            _index_cache_mtime = mtime
            
            _update_hot_index(_index_cache)
            
            duration = (time.time() - start_t) * 1000
            read_duration = (time.time() - read_start) * 1000
            logger.info(f"Loaded investment index: {len(_index_cache)} entries in {duration:.1f}ms")
            return _index_cache
        except Exception as e:
            logger.warning(f"Could not read investment index: {e}")
            return []

# Alias for backward compatibility
load = get_index

def rebuild(data_dir: Path, public_usi_dir: Path) -> int:
    """
    Scans all USIdata subdirectories and builds a unified index file.
    Returns number of entries indexed.
    """
    global _is_rebuilding, _index_cache, _index_cache_mtime
    
    # Concurrency guard: only one rebuild at a time
    with _rebuild_lock:
        if _is_rebuilding:
            logger.info("Index rebuild already in progress. Skipping duplicate request.")
            return 0
        _is_rebuilding = True

    try:
        import time
        start_t = time.time()
        entries = []
        
        from collections import defaultdict
        
        # Group by master_id OR usi_inv_id. Unmerged items stand alone identified by portal_id
        inv_groups = defaultdict(list)
        logger.info(f"Rebuilding investment index: Scanning {data_dir}...")
        rglob_start = time.time()
        usi_files = list(data_dir.rglob("usi_*.json"))
        rglob_duration = time.time() - rglob_start
        logger.info(f"Index rebuild: found {len(usi_files)} files in {rglob_duration:.2f}s via rglob")

        for usi_file in usi_files:
            if "usi_dev_" in usi_file.name: continue
            if usi_file.name.startswith("inv_master_"): continue
            
            try:
                data = json.loads(usi_file.read_text())
                usi_inv_id = data.get("usi_inv_id") or data.get("usi_id")
                
                if not usi_inv_id:
                    logger.error(f"Data Integrity Error: Missing usi_inv_id in {usi_file}")
                    continue

                uid = usi_inv_id
                inv_groups[uid].append((usi_file, data))
            except Exception as e:
                logger.error(f"Failed to read {usi_file}: {e}")
                continue
                
        for uid, group in inv_groups.items():
            # Pick the canonical usi_file for this ID
            canonical_item = None
            for p in ("rp", "oto", "to"):
                candidates = [item for item in group if item[0].name.startswith(f"usi_{p}_")]
                if candidates:
                    canonical_item = sorted(candidates, key=lambda x: x[0].name)[0]
                    break
            if not canonical_item:
                for legacy in ("usi_rp_", "usi_oto_", "usi_to_"):
                    candidates = [item for item in group if item[0].name.startswith(legacy)]
                    if candidates:
                        canonical_item = sorted(candidates, key=lambda x: x[0].name)[0]
                        break
            if not canonical_item:
                canonical_item = sorted(group, key=lambda x: x[0].name)[0]

            usi_file, data = canonical_item
            try:
                from python_worker.api.utils import _load_investment
                
                # Using _load_investment ensures consistent mapping between disk and index
                # fast_index=True skips expensive photo scans and identity lookups
                entry = _load_investment(data_dir=data_dir, public_usi_dir=public_usi_dir, system_id=uid, usi_file=usi_file, fast_index=True)
                if entry:
                    # OPTIMIZATION (06.01.08): Index only needs 1 thumbnail. Avoid bloating _index.json
                    if entry.get("photos"):
                        entry["photos"] = entry["photos"][:1]
                    entry.pop("image_urls", None)
                    entry.pop("nearby_investments", None)
                    
                    entries.append(entry)
            except Exception as e:
                logger.error(f"Failed to index {usi_file}: {e}")
                continue

        index = {
            "built_at": datetime.now().isoformat(),
            "count": len(entries),
            "entries": entries,
        }
        path = _index_path(data_dir)
        _atomic_write_json(path, index)
        
        total_duration = time.time() - start_t
        logger.info(f"Index rebuilt: {len(entries)} entries → {path} (total: {total_duration:.2f}s)")
        
        with _index_lock:
            _index_cache = entries
            _index_cache_mtime = path.stat().st_mtime
            _update_hot_index(_index_cache)
        
        _notify_change()
        return len(entries)
    except Exception as e:
        logger.exception(f"Index rebuild failed: {e}")
        return 0
    finally:
        with _rebuild_lock:
            _is_rebuilding = False

def upsert(data_dir: Path, public_usi_dir: Path, dev_slug: str = None, inv_slug: str = None, portal: str | None = None, inv_id: str | None = None) -> bool:
    """
    Recomputes and updates the index entry for a single investment.
    No-op (returns False) if index doesn't exist yet.
    """
    path = _index_path(data_dir)
    if not path.exists():
        return False

    from python_worker.api.utils import _load_investment
    entry = _load_investment(data_dir=data_dir, public_usi_dir=public_usi_dir, system_id=inv_id, fast_index=True)
    if not entry:
        return False

    # OPTIMIZATION (06.01.08): Index only needs 1 thumbnail. Avoid bloating _index.json
    if entry.get("photos"):
        entry["photos"] = entry["photos"][:1]
    entry.pop("image_urls", None)
    entry.pop("nearby_investments", None)

    try:
        index = json.loads(path.read_text())
    except Exception:
        return False

    entries = index.get("entries", [])

    # Replace existing or append
    replaced = False
    resolved_id = entry.get("usi_inv_id") or inv_id
    if resolved_id:
        for i, e in enumerate(entries):
            if e.get("usi_inv_id") == resolved_id:
                entries[i] = entry
                replaced = True
                break
    
    if not replaced:
        entries.append(entry)

    index["entries"] = entries
    index["count"] = len(entries)
    index["updated_at"] = datetime.now().isoformat()
    _atomic_write_json(path, index)
    
    global _index_cache, _index_cache_mtime
    with _index_lock:
        _index_cache = entries
        _index_cache_mtime = path.stat().st_mtime
        # --- KLUCZOWA POPRAWKA: Wymuszamy aktualizację słownika szybkich wyszukiwań ---
        _update_hot_index(_index_cache)
        
    logger.info(f"Successfully upserted investment ID {inv_id} to index and rebuilt hot mapping.")
    _notify_change()
    return True
