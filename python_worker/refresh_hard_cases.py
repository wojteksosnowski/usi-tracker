"""
Refresh hard-case investments from hard_cases_usimaster.csv:
1. Write ratings from USImaster into canonical meta_{inv_slug}_ratings.json
2. Queue all RP identifiers for process_batch (one network call per ID)
3. Run update_investment on each canonical (merges fresh data + ratings + images)

Run from repo root:
    python3 -m python_worker.refresh_hard_cases [--dry-run]
"""
import csv
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
HARD_CASES_CSV  = ROOT / "audit_output" / "hard_cases_usimaster.csv"
AUDIT_REPORT    = ROOT / "audit_output" / "duplicates_report.csv"
DATA_DIR        = ROOT / "Public" / "USIdata"


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_canonical_map() -> dict[str, str]:
    """inv_slug → canonical_dev_slug from the audit report."""
    m = {}
    with open(AUDIT_REPORT) as f:
        for r in csv.DictReader(f):
            m[r["inv_slug"]] = r["canonical_dev"]
    return m


def _extract_ratings(row: dict) -> dict:
    def _stars(s):
        if not s: return None
        table = {
            "★": 1, "★★": 2, "★★★": 3, "★★★★": 4,
            "⓿¾": 0.75, "★¼": 1.25, "★½": 1.5, "★¾": 1.75,
            "★★¼": 2.25, "★★½": 2.5, "★★¾": 2.75,
            "★★★¼": 3.25, "★★★½": 3.5, "★★★¾": 3.75,
        }
        return table.get(s.strip())

    def _f(v):
        if not v: return None
        try: return float(str(v).replace(",", "."))
        except ValueError: return None

    return {
        "status":       row.get("Ocena", "Brak"),
        "Gwiazdki":     _stars(row.get("Gwiazdki")),
        "Balkony":      _f(row.get("Balkony")),
        "Fasady":       _f(row.get("Fasady")),
        "Wnętrza":      _f(row.get("Wnętrza")),
        "Teren":        _f(row.get("Teren")),
        "Mieszkania":   _f(row.get("Mieszkania")),
        "Udogodnienia": _f(row.get("Udogodnienia")),
        "komentarz":    row.get("komentarz", "").strip(),
    }


def _has_any_rating(r: dict) -> bool:
    return any(v is not None for k, v in r.items() if k not in ("status", "komentarz"))


# ── main ─────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    canonical_map = _load_canonical_map()

    # Read hard cases — keep only RP rows (have rpID)
    rp_jobs: list[dict] = []
    seen: set[tuple[str, str]] = set()

    with open(HARD_CASES_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rp_id  = row.get("rpID", "").strip()
            inv_slug = row.get("USIfolder", "").strip()
            if not rp_id or not inv_slug:
                continue

            canonical_dev = canonical_map.get(inv_slug)
            if not canonical_dev:
                logger.warning("No canonical_dev for %s — skipping", inv_slug)
                continue

            key = (canonical_dev, inv_slug)
            ratings = _extract_ratings(row)

            if key not in seen:
                seen.add(key)
                rp_jobs.append({
                    "canonical_dev": canonical_dev,
                    "inv_slug":      inv_slug,
                    "rp_id":         rp_id,
                    "ratings":       ratings,
                })
            else:
                # Merge ratings: later row wins for non-null fields
                existing = next(j for j in rp_jobs if (j["canonical_dev"], j["inv_slug"]) == key)
                for k, v in ratings.items():
                    if v is not None:
                        existing["ratings"][k] = v

    logger.info("RP jobs to process: %d", len(rp_jobs))

    # Step 1 — write ratings to canonical meta files
    written = 0
    for job in rp_jobs:
        inv_dir = DATA_DIR / job["canonical_dev"] / job["inv_slug"]
        if not inv_dir.exists():
            logger.warning("Canonical dir missing: %s/%s — skipping", job["canonical_dev"], job["inv_slug"])
            continue
        meta_path = inv_dir / f"meta_{job['inv_slug']}_ratings.json"
        if not dry_run:
            meta_path.write_text(
                json.dumps(job["ratings"], indent=2, ensure_ascii=False), encoding="utf-8"
            )
        written += 1
        logger.info("[ratings] %s/%s → %s", job["canonical_dev"], job["inv_slug"], meta_path.name)

    logger.info("Ratings written: %d/%d", written, len(rp_jobs))
    if dry_run:
        logger.info("DRY RUN — no network calls, no files modified")
        return

    # Step 2 — send batch to usi-scrapers and update each investment
    from python_worker.config import get_scraper_config
    from usi_scrapers.fetcher import Fetcher
    from python_worker.services.investment_service import InvestmentService
    from usi_scrapers import api as scraper_api

    config  = get_scraper_config()
    fetcher = Fetcher(config)
    svc     = InvestmentService(config)

    # Collect RP identifiers (IDs)
    identifiers = [j["rp_id"] for j in rp_jobs
                   if (DATA_DIR / j["canonical_dev"] / j["inv_slug"]).exists()]

    logger.info("Sending %d RP identifiers to process_batch …", len(identifiers))

    def _on_progress(evt):
        pct = evt.get("progress_pct", 0)
        inv = evt.get("investment_slug") or evt.get("identifier", "?")
        status = evt.get("status", "")
        logger.info("  [%.0f%%] %s — %s", pct, inv, status)

    scraper_api.process_batch(
        config, fetcher, "rp", identifiers,
        on_progress=_on_progress,
        delay_range=(0.3, 1.0),
    )
    logger.info("process_batch done — running update_investment for each …")

    ok = 0
    fail = 0
    for job in rp_jobs:
        cdev, islug = job["canonical_dev"], job["inv_slug"]
        inv_dir = DATA_DIR / cdev / islug
        if not inv_dir.exists():
            continue
        try:
            result = svc.update_investment(cdev, islug, use_local_raw=True)
            if result:
                ok += 1
                logger.info("  ✓ %s/%s", cdev, islug)
            else:
                fail += 1
                logger.warning("  ✗ %s/%s (no data merged)", cdev, islug)
        except Exception as e:
            fail += 1
            logger.error("  ✗ %s/%s: %s", cdev, islug, e)

    logger.info("update_investment: %d ok, %d failed", ok, fail)
    logger.info("Done. Re-run audit_duplicates.py to see how many hard cases remain.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
