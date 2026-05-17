"""
Migrate investment files from legacy slug-based naming to portal-ID-based naming.

Old canonical: usi_{inv_slug}.json, usi_rp_{inv_slug}.json, usi_oto_{inv_slug}.json
New canonical: usi_{portal}_{portal_id}.json  (e.g. usi_rp_14563.json)

Also migrates raw_*.json and meta_*.json files when the portal ID is known.

Run dry-run first (default), then --apply to rename on disk.

Usage:
    python3 -m python_worker.migrate_inv_filenames            # dry-run
    python3 -m python_worker.migrate_inv_filenames --apply
    python3 -m python_worker.migrate_inv_filenames --apply --dev dom-development-sa
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def _primary_portal_id(sources: dict) -> tuple[str, str | None]:
    for portal in ("rp", "oto", "to"):
        pid = (sources.get(portal) or {}).get("id")
        if pid:
            return portal, str(pid)
    return "rp", None


def _legacy_candidates(inv_dir: Path, inv_slug: str):
    """Return all legacy-named usi_*.json files in inv_dir."""
    found = []
    for name in (
        f"usi_{inv_slug}.json",
        f"usi_rp_{inv_slug}.json",
        f"usi_oto_{inv_slug}.json",
        f"usi_to_{inv_slug}.json",
    ):
        p = inv_dir / name
        if p.exists():
            found.append(p)
    return found


def _already_new_format(inv_dir: Path) -> bool:
    """Return True if the directory already has a new-format canonical file."""
    for p in ("rp", "oto", "to"):
        for f in inv_dir.glob(f"usi_{p}_*.json"):
            # Exclude slug-based names like usi_rp_{slug}.json — they contain hyphens and letters
            # New format IDs are purely numeric (RP, TO) or alphanumeric-hash (OTO: IDxxxxxx)
            stem = f.stem  # e.g. "usi_rp_14563" or "usi_oto_ID4lulo"
            suffix = stem[len(f"usi_{p}_"):]
            if suffix and (suffix.isdigit() or (suffix.startswith("ID") and len(suffix) > 2)):
                return True
    return False


def migrate_investment(inv_dir: Path, inv_slug: str, apply: bool) -> dict:
    """
    Process one investment directory. Returns a result dict with action taken.
    """
    result = {"path": str(inv_dir), "inv_slug": inv_slug, "action": None, "detail": ""}

    if _already_new_format(inv_dir):
        result["action"] = "skip"
        result["detail"] = "already new format"
        return result

    legacy_files = _legacy_candidates(inv_dir, inv_slug)
    if not legacy_files:
        result["action"] = "skip"
        result["detail"] = "no legacy usi_*.json found"
        return result

    # Pick the best legacy file: prefer usi_{slug}.json, then rp, oto, to prefix variants
    canonical = inv_dir / f"usi_{inv_slug}.json"
    src = canonical if canonical in legacy_files else legacy_files[0]

    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except Exception as e:
        result["action"] = "error"
        result["detail"] = f"cannot read {src.name}: {e}"
        return result

    sources = data.get("sources", {})
    portal, portal_id = _primary_portal_id(sources)

    if not portal_id:
        result["action"] = "skip"
        result["detail"] = f"no portal ID in sources (file: {src.name})"
        return result

    new_name = f"usi_{portal}_{portal_id}.json"
    dst = inv_dir / new_name

    if dst.exists():
        result["action"] = "skip"
        result["detail"] = f"target {new_name} already exists"
        return result

    result["action"] = "rename"
    result["detail"] = f"{src.name} → {new_name}"

    # Also plan raw and meta migrations
    renames = [(src, dst)]

    # raw_{portal}_{inv_slug}.json → raw_{portal}_{portal_id}.json
    raw_src = inv_dir / f"raw_{portal}_{inv_slug}.json"
    if raw_src.exists():
        raw_dst = inv_dir / f"raw_{portal}_{portal_id}.json"
        if not raw_dst.exists():
            renames.append((raw_src, raw_dst))
            result["detail"] += f", {raw_src.name} → {raw_dst.name}"

    # meta_{inv_slug}_ratings.json → meta_{portal}_{portal_id}.json
    for meta_src_name in (
        f"meta_{inv_slug}_ratings.json",
        f"meta_rp_{inv_slug}.json",
        f"meta_oto_{inv_slug}.json",
        f"meta_to_{inv_slug}.json",
    ):
        meta_src = inv_dir / meta_src_name
        if meta_src.exists():
            meta_dst = inv_dir / f"meta_{portal}_{portal_id}.json"
            if not meta_dst.exists():
                renames.append((meta_src, meta_dst))
                result["detail"] += f", {meta_src.name} → {meta_dst.name}"
            break

    if apply:
        try:
            for s, d in renames:
                s.rename(d)
        except Exception as e:
            result["action"] = "error"
            result["detail"] = f"rename failed: {e}"

    return result


def run(data_dir: Path, apply: bool, dev_filter: str | None = None):
    total = skip = renamed = errors = 0

    for dev_dir in sorted(data_dir.iterdir()):
        if not dev_dir.is_dir():
            continue
        if dev_filter and dev_dir.name != dev_filter:
            continue

        for inv_dir in sorted(dev_dir.iterdir()):
            if not inv_dir.is_dir():
                continue

            total += 1
            r = migrate_investment(inv_dir, inv_dir.name, apply=apply)

            if r["action"] == "rename":
                renamed += 1
                logger.info(f"{'RENAME' if apply else 'WOULD RENAME'}  {r['detail']}  [{dev_dir.name}/{inv_dir.name}]")
            elif r["action"] == "error":
                errors += 1
                logger.error(f"ERROR  {r['detail']}  [{dev_dir.name}/{inv_dir.name}]")
            else:
                skip += 1
                logger.debug(f"skip  {r['detail']}  [{dev_dir.name}/{inv_dir.name}]")

    verb = "Renamed" if apply else "Would rename"
    logger.info(f"\nDone. Total: {total}, {verb}: {renamed}, Skipped: {skip}, Errors: {errors}")
    if not apply and renamed:
        logger.info("Run with --apply to execute renames.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Actually rename files (default: dry-run)")
    parser.add_argument("--dev", metavar="DEV_SLUG", help="Limit to one developer folder")
    parser.add_argument("--data-dir", metavar="PATH", help="Override USI_DATA_DIR (e.g. /Volumes/Samsam/Public/USIdata)")
    args = parser.parse_args()

    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        from python_worker.config import USI_DATA_DIR
        data_dir = Path(USI_DATA_DIR)

    logger.info(f"USI_DATA_DIR: {data_dir}")
    if not data_dir.exists():
        logger.error(f"Directory not found: {data_dir}")
        sys.exit(1)

    run(data_dir, apply=args.apply, dev_filter=args.dev)


if __name__ == "__main__":
    main()
