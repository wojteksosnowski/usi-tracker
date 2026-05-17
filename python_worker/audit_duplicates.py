"""
Audit script: find all USIdata investment folders whose dev_slug doesn't match
where usi_scrapers actually stored their images in Public/USI/.

Run from repo root:
    python3 -m python_worker.audit_duplicates [--output audit_output/]
"""
import json
import csv
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "Public" / "USIdata"
USI_DIR  = ROOT / "Public" / "USI"
DEV_DIR  = ROOT / "Public" / "USIdev"

# ── helpers ──────────────────────────────────────────────────────────────────

def _usi_inv_id(usi_file: Path) -> str | None:
    try:
        return json.loads(usi_file.read_text()).get("usi_inv_id")
    except Exception:
        return None


def _img_count(dev_slug: str, inv_slug: str) -> int:
    d = USI_DIR / dev_slug / inv_slug
    if not d.is_dir():
        return 0
    return sum(
        1 for p in d.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        and not p.name.startswith(".")
    )


def _has_dev_profile(dev_slug: str) -> bool:
    return (DEV_DIR / f"usi_dev_{dev_slug}.json").exists()


# ── main audit ───────────────────────────────────────────────────────────────

def run_audit() -> list[dict]:
    # Build index: inv_slug → {dev_slug: earliest_usi_inv_id}
    inv_index: dict[str, dict[str, str | None]] = defaultdict(dict)
    for inv_dir in DATA_DIR.glob("*/*"):
        if not inv_dir.is_dir():
            continue
        folder_dev = inv_dir.parts[-2]
        inv_slug   = inv_dir.parts[-1]
        usi_files  = sorted(inv_dir.glob("usi_*.json"))
        if not usi_files:
            continue
        # Use the first (alphabetically earliest) usi file's ID
        inv_index[inv_slug][folder_dev] = _usi_inv_id(usi_files[0])

    rows = []

    for inv_slug, dev_map in sorted(inv_index.items()):
        if len(dev_map) < 2:
            continue  # no cross-dev duplicate

        # For each version, count images in Public/USI/
        versions = []
        for dev_slug, inv_id in dev_map.items():
            img_n = _img_count(dev_slug, inv_slug)
            versions.append({
                "dev_slug": dev_slug,
                "inv_id":   inv_id or "NONE",
                "img_count": img_n,
                "has_profile": _has_dev_profile(dev_slug),
            })

        # Determine canonical:
        # 1. Version with most images wins
        # 2. Tie → lower usi_inv_id (older registration)
        def sort_key(v):
            try:
                numeric_id = int(v["inv_id"].split("-")[1]) if "-" in v["inv_id"] else 999999
            except Exception:
                numeric_id = 999999
            return (-v["img_count"], numeric_id)

        versions.sort(key=sort_key)
        canonical = versions[0]
        orphans   = versions[1:]

        for orphan in orphans:
            action = "REMOVE_ORPHAN"
            if canonical["img_count"] == 0 and orphan["img_count"] == 0:
                action = "NO_IMAGES_BOTH"
            elif orphan["img_count"] > 0:
                action = "BOTH_HAVE_IMAGES"

            rows.append({
                "inv_slug":           inv_slug,
                "canonical_dev":      canonical["dev_slug"],
                "canonical_inv_id":   canonical["inv_id"],
                "canonical_img_count": canonical["img_count"],
                "canonical_has_profile": canonical["has_profile"],
                "orphan_dev":         orphan["dev_slug"],
                "orphan_inv_id":      orphan["inv_id"],
                "orphan_img_count":   orphan["img_count"],
                "orphan_has_profile": orphan["has_profile"],
                "action":             action,
            })

    return rows


def write_report(rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    csv_path = output_dir / "duplicates_report.csv"
    fieldnames = [
        "inv_slug",
        "canonical_dev", "canonical_inv_id", "canonical_img_count", "canonical_has_profile",
        "orphan_dev", "orphan_inv_id", "orphan_img_count", "orphan_has_profile",
        "action",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # JSON
    json_path = output_dir / "duplicates_report.json"
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))

    # Summary
    from collections import Counter
    counts = Counter(r["action"] for r in rows)
    print(f"\nAudit complete — {len(rows)} pairs total:")
    for action, n in sorted(counts.items()):
        print(f"  {action:25s}: {n}")
    print(f"\nReport written to: {output_dir}/")


if __name__ == "__main__":
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "audit_output"
    rows = run_audit()
    write_report(rows, output_dir)
