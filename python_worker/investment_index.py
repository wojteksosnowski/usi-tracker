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
    return len(entries)


def load(data_dir: Path) -> list[dict] | None:
    """
    Returns list of investment entries from index, or None if index doesn't exist.
    """
    path = _index_path(data_dir)
    if not path.exists():
        return None
    try:
        index = json.loads(path.read_text())
        return index.get("entries", [])
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

    slug = f"{dev_slug}/{inv_slug}"
    entries = index.get("entries", [])

    # Replace existing or append
    replaced = False
    for i, e in enumerate(entries):
        if e.get("slug") == slug and e.get("developer_slug") == dev_slug:
            entries[i] = entry
            replaced = True
            break
    if not replaced:
        entries.append(entry)

    index["entries"] = entries
    index["count"] = len(entries)
    index["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(index, ensure_ascii=False))
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

    slug = f"{dev_slug}/{inv_slug}"
    before = len(index.get("entries", []))
    index["entries"] = [e for e in index.get("entries", []) if not (e.get("slug") == slug and e.get("developer_slug") == dev_slug)]
    if len(index["entries"]) == before:
        return False

    index["count"] = len(index["entries"])
    index["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(index, ensure_ascii=False))
    return True
