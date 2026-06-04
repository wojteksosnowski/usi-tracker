import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_index_cache = None
_index_cache_mtime = 0

def _index_path(data_dir: Path | str) -> Path:
    from pathlib import Path
    return Path(data_dir) / "_index.json"

def get_index(data_dir: Path) -> list:
    """Returns the list of indexed investments, cached in memory."""
    global _index_cache, _index_cache_mtime
    path = _index_path(data_dir)
    if not path.exists():
        return []
    
    mtime = path.stat().st_mtime
    if _index_cache is not None and mtime <= _index_cache_mtime:
        return _index_cache
        
    try:
        data = json.loads(path.read_text())
        _index_cache = data.get("entries", [])
        _index_cache_mtime = mtime
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
    entries = []
    
    from collections import defaultdict
    
    # Group by master_id OR usi_inv_id. Unmerged items stand alone identified by portal_id
    inv_groups = defaultdict(list)
    for usi_file in data_dir.rglob("usi_*.json"):
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
            dev_slug = usi_file.parent.parent.name
            inv_slug = usi_file.parent.name
            
            # Using _load_investment ensures consistent mapping between disk and index
            # fast_index=True skips expensive photo scans and identity lookups
            entry = _load_investment(data_dir=data_dir, public_usi_dir=public_usi_dir, system_id=uid, usi_file=usi_file, fast_index=True)
            if entry:
                # OPTIMIZATION: Index only needs 1 thumbnail. Avoid bloating _index.json
                if entry.get("photos"):
                    entry["photos"] = entry["photos"][:1]
                entry.pop("image_urls", None)
                
                entries.append(entry)
        except Exception as e:
            logger.error(f"Failed to index {usi_file}: {e}")
            continue

    index = {
        "built_at": datetime.now().isoformat(),
        "count": len(entries),
        "entries": entries,
    }
    _index_path(data_dir).write_text(json.dumps(index, ensure_ascii=False, indent=2))
    logger.info(f"Index rebuilt: {len(entries)} entries → {_index_path(data_dir)}")
    
    global _index_cache, _index_cache_mtime
    _index_cache = entries
    _index_cache_mtime = _index_path(data_dir).stat().st_mtime
    
    return len(entries)

def upsert(data_dir: Path, public_usi_dir: Path, dev_slug: str = None, inv_slug: str = None, portal: str | None = None, inv_id: str | None = None) -> bool:
    """
    Recomputes and updates the index entry for a single investment.
    No-op (returns False) if index doesn't exist yet.
    """
    path = _index_path(data_dir)
    if not path.exists():
        return False

    from python_worker.api.utils import _load_investment
    entry = _load_investment(data_dir=data_dir, public_usi_dir=public_usi_dir, system_id=inv_id)
    if not entry:
        return False

    # OPTIMIZATION: Index only needs 1 thumbnail. Avoid bloating _index.json
    if entry.get("photos"):
        entry["photos"] = entry["photos"][:1]
    entry.pop("image_urls", None)

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
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    
    global _index_cache, _index_cache_mtime
    _index_cache = entries
    _index_cache_mtime = path.stat().st_mtime
    return True
