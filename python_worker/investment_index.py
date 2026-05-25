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
    Scans all usi_*.json (Anchors) files, builds a fast search index.
    Returns number of entries indexed.
    """
    entries = []
    
    from usi_scrapers.mapping import get_mapping, resolve_path
    from collections import defaultdict
    
    # Group by master_id OR usi_inv_id. Unmerged items stand alone identified by portal_id
    inv_groups = defaultdict(list)
    for usi_file in data_dir.rglob("usi_*.json"):
        if "usi_dev_" in usi_file.name: continue
        if usi_file.name.startswith("inv_master_"): continue
        
        try:
            data = json.loads(usi_file.read_text())
            usi_inv_id = data.get("usi_inv_id") or data.get("usi_id")
            
            if usi_inv_id:
                uid = usi_inv_id
            else:
                portal = data.get("portal")
                portal_id = data.get("portal_id")
                if portal and portal_id:
                    uid = f"{portal}_{portal_id}"
                else:
                    uid = f"legacy_{usi_file.parent.parent.name}/{usi_file.parent.name}"
            
            inv_groups[uid].append((usi_file, data))
        except Exception:
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
            # Determine portal and portal_id from sources (Unified Schema) or root (Skeletons)
            sources = data.get("sources") or {}
            portal = data.get("portal")
            portal_id = data.get("portal_id")
            
            if not portal and sources:
                # Find the primary portal from sources
                for p in ("rp", "oto", "to"):
                    if p in sources:
                        portal = p
                        portal_id = sources[p].get("id")
                        break
                if not portal:
                    portal = list(sources.keys())[0]
                    portal_id = sources[portal].get("id")
            
            # Robust extraction of names and developer
            name = data.get("name")
            developer = data.get("developer")
            
            # Fallback for skeletons: read raw/meta
            raw = {}
            if not name or not developer:
                raw_file_name = data.get("raw_file")
                raw_path = usi_file.parent / raw_file_name if raw_file_name else None
                if not raw_path or not raw_path.exists():
                    # Find any raw file for this portal in the directory
                    matches = sorted(list(usi_file.parent.glob(f"raw_{portal}_*.json")))
                    if matches: raw_path = matches[-1]
                
                if raw_path and raw_path.exists():
                    try:
                        raw = json.loads(raw_path.read_text())
                    except: pass

            meta = {}
            meta_file_name = data.get("meta_file")
            meta_path = usi_file.parent / meta_file_name if meta_file_name else None
            if meta_path and meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                except: pass

            mapping = get_mapping(portal) if portal else {}
            def _get(key, fallback=None):
                path = mapping.get(key)
                if not path: return fallback
                val = resolve_path(raw, path)
                return val if val is not None else fallback

            dev_slug = data.get("developer_slug") or _get("developer_slug") or usi_file.parent.parent.name
            inv_slug = data.get("investment_slug") or _get("slug") or usi_file.parent.name
            
            # Photos logic for index (similar to api/utils.py)
            photos = []
            image_paths = data.get("image_paths") or []
            if image_paths:
                for p in image_paths:
                    p_clean = p.lstrip("/")
                    if p_clean.startswith("Public/USI/"):
                        photos.append("/api/image/" + p_clean[len("Public/USI/"):])
            
            if not photos:
                photos = data.get("image_urls") or []
            
            if not photos:
                img_list = meta.get("ratings", {}).get("imgList")
                if img_list:
                    for p in [x.strip() for x in img_list.split(",") if x.strip()]:
                        p_clean = p.lstrip("/")
                        if p_clean.startswith("Public/USI/"):
                            photos.append("/api/image/" + p_clean[len("Public/USI/"):])
            
            loc = data.get("location") or {}
            specs = data.get("specifications") or {}
            fin = data.get("financials") or {}

            entries.append({
                "id": uid,
                "usi_inv_id": data.get("usi_inv_id") or data.get("usi_id"),
                "usi_dev_id": data.get("usi_dev_id"),
                "portal_id": portal_id,
                "portal": portal,
                "source": portal,
                "slug": f"{dev_slug}/{inv_slug}",
                "developer_slug": dev_slug,
                "investment_slug": inv_slug,
                "developer": developer or _get("developer_name") or data.get("developer"),
                "name": name or _get("name") or meta.get("name"),
                "status": data.get("status") or _get("status") or meta.get("status"),
                "district": loc.get("district") or (ad_loc := _get("location")) and isinstance(ad_loc, dict) and ad_loc.get("district"),
                "city": loc.get("city") or (ad_loc := _get("location")) and isinstance(ad_loc, dict) and ad_loc.get("city"),
                "delivery": specs.get("delivery_date") or _get("delivery_raw"),
                "price_m2_min": fin.get("price_m2_min") or _get("price_min"),
                "price_m2_max": fin.get("price_m2_max") or _get("price_max"),
                "price_avg": fin.get("price_avg"),
                "photos": photos,
                "ratings": meta.get("ratings", {}),
                "segment": specs.get("segment") or _get("specifications.segment"),
                "master_id": data.get("master_id")
            })
        except Exception as e:
            logger.error(f"Failed to index {usi_file}: {e}")
            continue

    index = {
        "built_at": datetime.now().isoformat(),
        "count": len(entries),
        "entries": entries,
    }
    _index_path(data_dir).write_text(json.dumps(index, ensure_ascii=False))
    logger.info(f"Index rebuilt: {len(entries)} entries → {_index_path(data_dir)}")
    
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
