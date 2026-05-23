"""
Disk-based investment index for fast list-view serving.

The index (_index.json in USIdata root) stores one pre-computed entry per investment —
the same shape returned by _load_investment(). The list endpoint reads this single file
instead of scanning ~7 500 individual usi_*.json files on every request.

Kept in sync by:
  - rebuild()   : full scan, run once at startup or via CLI/API
  - upsert()    : called after every update_investment() / register_investment()
  - remove()    : called if an investment is deleted
"""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_INDEX_FILENAME = "_index.json"


def _index_path(data_dir: Path) -> Path:
    return data_dir / _INDEX_FILENAME


def rebuild(data_dir: Path, public_usi_dir: Path) -> int:
    """
    Scans all usi_*.json files, computes full _load_investment() entries, saves index.
    Returns number of entries indexed.
    """
    from python_worker.api.utils import _load_investment

    entries = []
    skipped = 0

    # 1. Pre-load all master files
    masters = {}
    for mf in data_dir.rglob("inv_master_*.json"):
        try:
            m_data = json.loads(mf.read_text(encoding="utf-8"))
            if m_data.get("inv_master_id"):
                masters[m_data["inv_master_id"]] = m_data
        except Exception as e:
            logger.warning(f"Error reading {mf}: {e}")

    for dev_dir in sorted(data_dir.iterdir()):
        if not dev_dir.is_dir() or dev_dir.name.startswith("_") or dev_dir.name.startswith("."):
            continue
        for inv_dir in sorted(dev_dir.iterdir()):
            if not inv_dir.is_dir():
                continue
            usi_files = list(inv_dir.glob("usi_*.json"))
            for usi_file in usi_files:
                parts = usi_file.name.split("_")
                portal = parts[1] if len(parts) == 3 else None
                entry = _load_investment(
                    dev_dir.name, inv_dir.name,
                    data_dir=data_dir, public_usi_dir=public_usi_dir,
                    portal=portal,
                )
                if entry:
                    master_id = entry.get("master_id")
                    if master_id and master_id in masters:
                        entry["merged_from"] = masters[master_id].get("merged_from", [])
                        entry["master_usi_inv_id"] = masters[master_id].get("master_usi_inv_id")
                    entries.append(entry)
                else:
                    skipped += 1

    index = {
        "built_at": datetime.now().isoformat(),
        "count": len(entries),
        "entries": entries,
    }
    _index_path(data_dir).write_text(json.dumps(index, ensure_ascii=False))
    logger.info(f"Index rebuilt: {len(entries)} entries, {skipped} skipped → {_index_path(data_dir)}")
    
    global _index_cache, _index_cache_mtime
    _index_cache = None
    _index_cache_mtime = 0
    
    return len(entries)


_index_cache = None
_index_cache_mtime = 0

def load(data_dir: Path) -> list[dict] | None:
    """
    Returns list of investment entries from index, or None if index doesn't exist.
    """
    global _index_cache, _index_cache_mtime
    path = _index_path(data_dir)
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        if _index_cache is not None and mtime == _index_cache_mtime:
            return _index_cache
            
        index = json.loads(path.read_text())
        _index_cache = index.get("entries", [])
        _index_cache_mtime = mtime
        return _index_cache
    except Exception as e:
        logger.warning(f"Could not read investment index: {e}")
        return None


def upsert(data_dir: Path, public_usi_dir: Path, dev_slug: str, inv_slug: str, portal: str | None = None) -> bool:
    """
    Recomputes and updates the index entry for a single investment.
    No-op (returns False) if index doesn't exist yet.
    """
    path = _index_path(data_dir)
    if not path.exists():
        return False

    from python_worker.api.utils import _load_investment
    entry = _load_investment(dev_slug, inv_slug, data_dir=data_dir, public_usi_dir=public_usi_dir, portal=portal)
    if not entry:
        return False

    # Enrich with master data if needed
    master_id = entry.get("master_id")
    if master_id:
        # Find the master file. We can search for it in data_dir.
        for mf in data_dir.rglob(f"inv_master_{master_id}.json"):
            try:
                m_data = json.loads(mf.read_text(encoding="utf-8"))
                entry["merged_from"] = m_data.get("merged_from", [])
                entry["master_usi_inv_id"] = m_data.get("master_usi_inv_id")
                break
            except Exception:
                pass

    try:
        index = json.loads(path.read_text())
    except Exception:
        return False

    entries = index.get("entries", [])

    # Replace existing or append
    replaced = False
    inv_id = entry.get("usi_inv_id")
    if inv_id:
        for i, e in enumerate(entries):
            if e.get("usi_inv_id") == inv_id:
                entries[i] = entry
                replaced = True
                break
    else:
        # Fallback for legacy data without IDs
        slug = f"{dev_slug}/{inv_slug}"
        for i, e in enumerate(entries):
            if e.get("slug") == slug and e.get("developer_slug") == dev_slug and not e.get("usi_inv_id"):
                entries[i] = entry
                replaced = True
                break

    if not replaced:
        entries.append(entry)

    index["entries"] = entries
    index["count"] = len(entries)
    index["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(index, ensure_ascii=False))
    
    global _index_cache, _index_cache_mtime
    _index_cache = None
    _index_cache_mtime = 0
    
    return True


def remove(data_dir: Path, dev_slug: str, inv_slug: str) -> bool:
    """Removes a single investment entry from the index."""
    path = _index_path(data_dir)
    if not path.exists():
        return False
    try:
        index = json.loads(path.read_text())
    except Exception:
        return False

    before = len(index.get("entries", []))
    
    # We remove by slug as it's a folder-wide sweep. 
    # If one portal is removed but folder stays, it's handled by upsert() of the remaining one.
    slug = f"{dev_slug}/{inv_slug}"
    index["entries"] = [e for e in index.get("entries", []) if not (e.get("slug") == slug and e.get("developer_slug") == dev_slug)]
    if len(index["entries"]) == before:
        return False

    index["count"] = len(index["entries"])
    index["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(index, ensure_ascii=False))
    
    global _index_cache, _index_cache_mtime
    _index_cache = None
    _index_cache_mtime = 0
    
    return True
