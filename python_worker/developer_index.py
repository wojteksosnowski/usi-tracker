"""
Disk-based developer index for fast list-view serving and slug/ID lookups.

The index (_dev_index.json in USIdev root) stores one pre-computed entry per developer.
This avoids scanning potentially thousands of usi_dev_*.json files across multiple formats.

Kept in sync by:
  - rebuild()   : full scan, run once at startup or via CLI
  - upsert()    : called after every developer save/update
  - remove()    : called if a developer is deleted
"""
import json
import logging
import os
from filelock import FileLock
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_INDEX_FILENAME = "_dev_index.json"

_on_change_callbacks = []

def on_change(callback):
    """Register a callback to be called whenever the developer index is updated or rebuilt."""
    _on_change_callbacks.append(callback)

def _notify_change():
    """Triggers all registered change callbacks."""
    for cb in _on_change_callbacks:
        try:
            cb()
        except Exception as e:
            logger.error(f"Error in developer_index change callback: {e}")


def _index_path(dev_dir: Path) -> Path:
    return dev_dir / _INDEX_FILENAME


@contextmanager
def _index_lock(dev_dir: Path):
    """Provides an exclusive lock for writing to the index to prevent race conditions."""
    lock_path = _index_path(dev_dir).with_suffix('.lock')
    with FileLock(str(lock_path)):
        yield


def _write_atomic(path: Path, data: dict):
    """Writes JSON data atomically to prevent corrupted reads."""
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix="._dev_index_", suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise


def rebuild(data_dir: Path, dev_dir: Path) -> int:
    """
    Scans all developer files, enriches them with master data, and saves the index.
    Returns the number of entries indexed.
    """
    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(data_dir, dev_dir)

    entries = []
    seen_ids = set()
    identifiers = dm.indexer.get_existing_identifiers()

    def _add(candidate_path: Path):
        try:
            data = json.loads(candidate_path.read_text(encoding="utf-8"))
            dev_id = data.get("usi_dev_id")
            if not dev_id:
                # Should not happen for valid files, but just in case
                return

            if dev_id in seen_ids:
                return

            seen_ids.add(dev_id)
            
            # Fast path: enrich the data we ALREADY read from disk directly,
            # bypassing the O(N^2) disk scan caused by dm.get_developer_by_id finding the anchor.
            enriched = dm.repo._enrich_with_master(data, identifiers)
            if enriched:
                entries.append(enriched)
            else:
                entries.append(data)
        except Exception as e:
            logger.warning(f"Error reading dev file for index {candidate_path}: {e}")

    # New format / canonical format inside subdirs
    for candidate in dev_dir.glob("*/usi_dev_*.json"):
        _add(candidate)

    # Legacy flat format
    for candidate in dev_dir.glob("usi_dev_*.json"):
        _add(candidate)

    # Legacy format in data_dir
    for candidate in data_dir.glob("*/usi_dev_*.json"):
        _add(candidate)

    index = {
        "built_at": datetime.now().isoformat(),
        "count": len(entries),
        "entries": entries,
    }
    
    with _index_lock(dev_dir):
        _write_atomic(_index_path(dev_dir), index)
        
    logger.info(f"Developer index rebuilt: {len(entries)} entries → {_index_path(dev_dir)}")
    _notify_change()
    return len(entries)


_dev_index_cache = None
_dev_index_cache_mtime = 0

def load(dev_dir: Path) -> list[dict] | None:
    """
    Returns list of developer entries from index, or None if index doesn't exist.
    """
    global _dev_index_cache, _dev_index_cache_mtime
    path = _index_path(dev_dir)
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        if _dev_index_cache is not None and mtime == _dev_index_cache_mtime:
            return _dev_index_cache
            
        index = json.loads(path.read_text(encoding="utf-8"))
        _dev_index_cache = index.get("entries", [])
        _dev_index_cache_mtime = mtime
        return _dev_index_cache
    except Exception as e:
        logger.warning(f"Could not read developer index: {e}")
        return None


def upsert(data_dir: Path, dev_dir: Path, dev_slug: str, usi_dev_id: str) -> bool:
    """
    Recomputes and updates the index entry for a single developer.
    No-op (returns False) if index doesn't exist yet.
    """
    path = _index_path(dev_dir)
    if not path.exists():
        return False

    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(data_dir, dev_dir)
    entry = dm.get_developer_by_id(usi_dev_id)
    if not entry:
        return False

    with _index_lock(dev_dir):
        if not path.exists():
            return False
        try:
            index = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False

        entries = index.get("entries", [])
        replaced = False

        for i, e in enumerate(entries):
            if e.get("usi_dev_id") == usi_dev_id:
                entries[i] = entry
                replaced = True
                break
            # Fallback for devs without usi_dev_id indexed previously (should be rare)
            elif not e.get("usi_dev_id") and e.get("developer_slug") == dev_slug:
                entries[i] = entry
                replaced = True
                break

        if not replaced:
            entries.append(entry)

        index["entries"] = entries
        index["count"] = len(entries)
        index["updated_at"] = datetime.now().isoformat()
        
        _write_atomic(path, index)
        
        global _dev_index_cache, _dev_index_cache_mtime
        _dev_index_cache = None
        _dev_index_cache_mtime = 0
        
        _notify_change()
        return True


def remove(dev_dir: Path, usi_dev_id: str) -> bool:
    """Removes a single developer entry from the index by ID."""
    path = _index_path(dev_dir)
    if not path.exists():
        return False
        
    with _index_lock(dev_dir):
        if not path.exists():
            return False
        try:
            index = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False

        entries = index.get("entries", [])
        before = len(entries)
        entries = [e for e in entries if e.get("usi_dev_id") != usi_dev_id]

        if len(entries) == before:
            return False

        index["entries"] = entries
        index["count"] = len(entries)
        index["updated_at"] = datetime.now().isoformat()
        _write_atomic(path, index)
        
    _notify_change()
    return True

# -------------------------------------------------------------------------
# Dev Master Index (Level 3)
# -------------------------------------------------------------------------

def _master_index_path(dev_dir: Path) -> Path:
    return dev_dir / "_dev_master_index.json"

def rebuild_master_index(dev_dir: Path) -> dict:
    """
    Scans all dev_master_*.json files and creates an index mapping master_id to its directory/file.
    """
    master_index = {}
    for path in dev_dir.glob("*/dev_master_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            master_id = data.get("dev_master_id")
            if master_id:
                master_index[master_id] = {
                    "path": path.parent.name,
                    "master_usi_dev_id": data.get("master_usi_dev_id")
                }
        except Exception as e:
            logger.warning(f"Failed to read dev_master for index: {path} - {e}")
            
    index_data = {
        "built_at": datetime.now().isoformat(),
        "entries": master_index
    }
    
    with _index_lock(dev_dir):
        _write_atomic(_master_index_path(dev_dir), index_data)
        
    global _dev_master_index_cache, _dev_master_index_cache_mtime
    _dev_master_index_cache = None
    _dev_master_index_cache_mtime = 0
    
    logger.info(f"Dev Master index rebuilt: {len(master_index)} entries → {_master_index_path(dev_dir)}")
    return master_index

_dev_master_index_cache = None
_dev_master_index_cache_mtime = 0

def load_master_index(dev_dir: Path) -> dict | None:
    """Returns mapping of master_id -> dict(path, master_usi_dev_id)."""
    global _dev_master_index_cache, _dev_master_index_cache_mtime
    path = _master_index_path(dev_dir)
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        if _dev_master_index_cache is not None and mtime == _dev_master_index_cache_mtime:
            return _dev_master_index_cache
            
        data = json.loads(path.read_text(encoding="utf-8"))
        _dev_master_index_cache = data.get("entries", {})
        _dev_master_index_cache_mtime = mtime
        return _dev_master_index_cache
    except Exception as e:
        logger.warning(f"Could not read dev_master index: {e}")
        return None

def upsert_master(dev_dir: Path, master_data: dict, folder_name: str) -> bool:
    path = _master_index_path(dev_dir)
    if not path.exists():
        return False
    master_id = master_data.get("dev_master_id")
    if not master_id:
        return False
        
    with _index_lock(dev_dir):
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False
            
        entries = data.setdefault("entries", {})
        entries[master_id] = {
            "path": folder_name,
            "master_usi_dev_id": master_data.get("master_usi_dev_id")
        }
        data["updated_at"] = datetime.now().isoformat()
        
        _write_atomic(path, data)
        
        global _dev_master_index_cache, _dev_master_index_cache_mtime
        _dev_master_index_cache = None
        _dev_master_index_cache_mtime = 0
        return True
