"""
Brute-force OTO refresh for hard-case investments from hard_cases_usimaster.csv.

For each unique investment:
1. Try every stored Otodom URL until one returns valid data
2. If successful: write ratings to canonical meta file, run update_investment
3. Remove successfully imported investments from hard_cases_usimaster.csv

Run from repo root:
    python3 -m python_worker.refresh_hard_cases_oto [--dry-run]
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT           = Path(__file__).parent.parent
HARD_CASES_CSV = ROOT / "audit_output" / "hard_cases_usimaster.csv"
AUDIT_REPORT   = ROOT / "audit_output" / "duplicates_report.csv"
DATA_DIR       = ROOT / "Public" / "USIdata"


def _load_canonical_map() -> dict[str, str]:
    m = {}
    with open(AUDIT_REPORT, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            m[r["inv_slug"]] = r["canonical_dev"]
    return m


def _extract_ratings(row: dict) -> dict:
    def _stars(s):
        if not s:
            return None
        table = {
            "★": 1, "★★": 2, "★★★": 3, "★★★★": 4,
            "⓿¾": 0.75, "★¼": 1.25, "★½": 1.5, "★¾": 1.75,
            "★★¼": 2.25, "★★½": 2.5, "★★¾": 2.75,
            "★★★¼": 3.25, "★★★½": 3.5, "★★★¾": 3.75,
        }
        return table.get(s.strip())

    def _f(v):
        if not v:
            return None
        try:
            return float(str(v).replace(",", "."))
        except ValueError:
            return None

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


def _merge_ratings(base: dict, extra: dict) -> dict:
    result = dict(base)
    for k, v in extra.items():
        if v is not None:
            result[k] = v
    return result


def _build_jobs(canonical_map: dict) -> list[dict]:
    """Group CSV rows by inv_slug; collect all OTO URLs and merge ratings."""
    groups: dict[str, dict] = {}

    with open(HARD_CASES_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            slug = row.get("USIfolder", "").strip()
            if not slug:
                continue
            canonical_dev = canonical_map.get(slug)
            if not canonical_dev:
                logger.warning("No canonical_dev for %s — skipping", slug)
                continue

            url = row.get("strona_otodom", "").strip()

            if slug not in groups:
                groups[slug] = {
                    "inv_slug":      slug,
                    "canonical_dev": canonical_dev,
                    "oto_urls":      [],
                    "ratings":       _extract_ratings(row),
                }
            else:
                # Merge ratings: later row wins for non-null fields
                groups[slug]["ratings"] = _merge_ratings(
                    groups[slug]["ratings"], _extract_ratings(row)
                )

            if url and url not in groups[slug]["oto_urls"]:
                groups[slug]["oto_urls"].append(url)

    return list(groups.values())


def main(dry_run: bool = False) -> None:
    canonical_map = _load_canonical_map()
    jobs = _build_jobs(canonical_map)
    logger.info("OTO jobs to attempt: %d", len(jobs))

    from python_worker.config import get_scraper_config
    from usi_scrapers.fetcher import Fetcher
    from python_worker.services.investment_service import InvestmentService
    from usi_scrapers import api as scraper_api

    config  = get_scraper_config()
    fetcher = Fetcher(config)
    svc     = InvestmentService(config)

    ok_slugs: list[str] = []
    fail_slugs: list[str] = []

    for job in jobs:
        cdev   = job["canonical_dev"]
        islug  = job["inv_slug"]
        urls   = job["oto_urls"]
        inv_dir = DATA_DIR / cdev / islug

        if not inv_dir.exists():
            logger.warning("  [%s/%s] canonical dir missing — skipping", cdev, islug)
            fail_slugs.append(islug)
            continue

        if not urls:
            logger.warning("  [%s/%s] no OTO URLs — skipping", cdev, islug)
            fail_slugs.append(islug)
            continue

        logger.info("[%s/%s] trying %d OTO URL(s)…", cdev, islug, len(urls))
        fetched = False

        for url in urls:
            logger.info("  → %s", url)
            if dry_run:
                logger.info("  DRY RUN — skipping actual fetch")
                continue
            try:
                result = scraper_api.fetch_investment(config, fetcher, "oto", url)
                if result and not result.get("error"):
                    logger.info("  ✓ fetch ok")
                    fetched = True
                    break
                else:
                    logger.info("  ✗ %s", result.get("error", "no data") if result else "null")
            except Exception as e:
                logger.warning("  ✗ exception: %s", e)

        if dry_run:
            continue

        if not fetched:
            logger.warning("  [%s/%s] all URLs failed — skipping", cdev, islug)
            fail_slugs.append(islug)
            continue

        # Write ratings
        meta_path = inv_dir / f"meta_{islug}_ratings.json"
        meta_path.write_text(
            json.dumps(job["ratings"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("  [ratings] written → %s", meta_path.name)

        # Run update_investment
        try:
            update_result = svc.update_investment(cdev, islug, use_local_raw=True)
            if update_result:
                logger.info("  ✓ update_investment ok → %s/%s", cdev, islug)
                ok_slugs.append(islug)
            else:
                logger.warning("  ✗ update_investment returned no data for %s/%s", cdev, islug)
                fail_slugs.append(islug)
        except Exception as e:
            logger.error("  ✗ update_investment error for %s/%s: %s", cdev, islug, e)
            fail_slugs.append(islug)

    logger.info("Results: %d ok, %d failed", len(ok_slugs), len(fail_slugs))

    if dry_run or not ok_slugs:
        if dry_run:
            logger.info("DRY RUN — no files modified")
        return

    # Remove successful slugs from hard_cases_usimaster.csv
    ok_set = set(ok_slugs)
    remaining: list[dict] = []
    removed = 0

    with open(HARD_CASES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            if row.get("USIfolder", "").strip() in ok_set:
                removed += 1
            else:
                remaining.append(row)

    with open(HARD_CASES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining)

    logger.info("Removed %d rows from hard_cases_usimaster.csv (%d rows remain)", removed, len(remaining))

    if ok_slugs:
        logger.info("Successfully imported: %s", ", ".join(ok_slugs))
    if fail_slugs:
        logger.info("Still failing: %s", ", ".join(fail_slugs))


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
