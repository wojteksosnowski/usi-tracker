"""
Audit script: detect unmerged developer duplicates in USIdev/.

Section A: Pairs in suggestions[] where neither record is a merged child.
Section B: Dev records missing OTO/RP that Konkurenci.csv could supply from another row.

Usage:
    python3 python_worker/audit_dev_duplicates.py
    python3 python_worker/audit_dev_duplicates.py --min-score 0.85
"""
import csv
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
USI_DEV_DIR = BASE / "Public/USIdev"
USI_DATA_DIR = BASE / "Public/USIdata"
KONKURENCI_CSV = BASE / "reference-data/coda/Konkurenci.csv"

def _oto_ids(pm_oto: dict) -> list[str]:
    if not pm_oto:
        return []
    ids = pm_oto.get("agency_ids") or ([pm_oto["agency_id"]] if pm_oto.get("agency_id") else [])
    return ids

def _rp_id(pm_rp: dict) -> str:
    if not pm_rp:
        return "brak"
    return pm_rp.get("id") or pm_rp.get("slug") or "brak"

def _inv_count(dev_slug: str) -> int:
    d = USI_DATA_DIR / dev_slug
    if not d.is_dir():
        return 0
    return sum(1 for p in d.iterdir() if p.is_dir())


def _build_child_ids(dev_dir: Path) -> set[str]:
    child_ids: set[str] = set()
    for master_file in dev_dir.glob("*/dev_master_*.json"):
        try:
            m = json.loads(master_file.read_text(encoding="utf-8"))
            for entry in m.get("merged_from", []):
                if cid := entry.get("usi_dev_id"):
                    child_ids.add(cid)
        except Exception:
            pass
    return child_ids


def section_a(devs: dict, min_score: float):
    print(f"\n{'═'*72}")
    print(f"SEKCJA A — Niescalone pary (suggestions, żadna nie jest dzieckiem DM), score >= {min_score}")
    print(f"{'═'*72}")

    child_ids = _build_child_ids(USI_DEV_DIR)
    seen = set()
    pairs = []

    for dev_id, rec in devs.items():
        if dev_id in child_ids:
            continue
        for sug in rec.get("suggestions") or []:
            score = sug.get("score", 0)
            if score < min_score:
                continue
            other_id = sug.get("usi_dev_id")
            other = devs.get(other_id)
            if not other or other_id in child_ids:
                continue
            key = tuple(sorted([dev_id, other_id]))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((score, rec, other, sug.get("reason", "")))

    pairs.sort(key=lambda x: -x[0])

    if not pairs:
        print("  Brak niescalonych par.")
        return

    for score, a, b, reason in pairs:
        pm_a = a.get("portal_mapping") or {}
        pm_b = b.get("portal_mapping") or {}
        oto_a = _oto_ids(pm_a.get("oto"))
        oto_b = _oto_ids(pm_b.get("oto"))
        oto_diff = "← różne" if set(oto_a) != set(oto_b) else ""
        print(f"\n[score={score:.2f}] {a['developer_slug']} ({a['usi_dev_id']}) ↔ {b['developer_slug']} ({b['usi_dev_id']})")
        print(f"  Powód : {reason}")
        print(f"  RP    : {_rp_id(pm_a.get('rp'))} ↔ {_rp_id(pm_b.get('rp'))}")
        print(f"  OTO   : {oto_a} ↔ {oto_b}  {oto_diff}")
        print(f"  Inwest: {_inv_count(a['developer_slug'])} ↔ {_inv_count(b['developer_slug'])}")

    print(f"\nŁącznie: {len(pairs)} niescalonych par")


def section_b(devs: dict):
    print(f"\n{'═'*72}")
    print(f"SEKCJA B — Devy z brakującymi IDs możliwymi do uzupełnienia z Konkurenci.csv")
    print(f"{'═'*72}")

    if not KONKURENCI_CSV.exists():
        print("  Brak Konkurenci.csv — pomijam.")
        return

    # Build {usiFolder -> [{rp_id, rp_slug, oto_id, oto_slug},...]} from CSV
    csv_rows: dict[str, list[dict]] = {}
    with open(KONKURENCI_CSV, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            slug = row.get("usiFolder", "").strip()
            if not slug:
                continue
            csv_rows.setdefault(slug, []).append({
                "rp_id":   row.get("rpID", "").strip(),
                "rp_slug": row.get("rpSlug", "").strip(),
                "oto_id":  re.sub(r"^ID", "", row.get("otoID", "").strip()),
                "oto_slug": row.get("otoSlug", "").strip(),
            })

    # Build a map of all OTO IDs present anywhere in USIdev for fast lookup
    all_oto_ids: dict[str, str] = {}  # oto_id -> dev_slug that holds it
    for rec in devs.values():
        for oid in _oto_ids((rec.get("portal_mapping") or {}).get("oto")):
            all_oto_ids[oid] = rec.get("developer_slug", "?")

    issues = []
    # Index devs by slug for faster (but potentially multi-result) lookup
    devs_by_slug: dict[str, list[dict]] = {}
    for d in devs.values():
        slug = d.get("developer_slug")
        if slug:
            devs_by_slug.setdefault(slug, []).append(d)

    for dev_slug, rows in csv_rows.items():
        dev_file = USI_DEV_DIR / dev_slug / f"usi_dev_{dev_slug}.json"
        if not dev_file.exists():
            continue
            
        matches = devs_by_slug.get(dev_slug, [])
        if not matches:
            try:
                matches = [json.loads(dev_file.read_text(encoding="utf-8"))]
            except Exception:
                continue

        for rec in matches:
            pm = rec.get("portal_mapping") or {}
            existing_oto = _oto_ids(pm.get("oto"))

            truly_missing_oto = []
            for row in rows:
                oid = row["oto_id"]
                if not oid:
                    continue
                if oid in existing_oto:
                    continue  # present in this record
                oto_slug = row["oto_slug"]
                if oto_slug and oto_slug != dev_slug and oid in all_oto_ids:
                    continue  # correctly split to otoSlug record
                truly_missing_oto.append(oid)

            has_rp = bool(pm.get("rp"))
            csv_has_rp = any(r["rp_id"] or r["rp_slug"] for r in rows)
            missing_rp = not has_rp and csv_has_rp

            if truly_missing_oto or missing_rp:
                issues.append((dev_slug, rec.get("usi_dev_id", "?"), missing_rp, truly_missing_oto))

    if not issues:
        print("  Brak niezgodności.")
        return

    for dev_slug, dev_id, missing_rp, missing_oto in sorted(issues):
        parts = []
        if missing_rp:
            parts.append("brak RP (jest w CSV)")
        if missing_oto:
            parts.append(f"brak OTO: {missing_oto}")
        print(f"  {dev_slug} ({dev_id}): {'; '.join(parts)}")

    print(f"\nŁącznie: {len(issues)} rekordów do uzupełnienia")


def main():
    min_score = 1.0
    if "--min-score" in sys.argv:
        idx = sys.argv.index("--min-score")
        min_score = float(sys.argv[idx + 1])

    print(f"Ładowanie USIdev/ ({USI_DEV_DIR})...")
    devs = {}
    seen_slugs = set()
    # Canonical: USIdev/{slug}/usi_dev_{slug}.json
    for f in USI_DEV_DIR.glob("*/usi_dev_*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
            dev_id = rec.get("usi_dev_id")
            if dev_id:
                devs[dev_id] = rec
                seen_slugs.add(rec.get("developer_slug", ""))
        except Exception:
            pass
    # Legacy flat: USIdev/usi_dev_{slug}.json
    for f in USI_DEV_DIR.glob("usi_dev_*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
            slug = rec.get("developer_slug", "")
            if slug in seen_slugs:
                continue
            dev_id = rec.get("usi_dev_id")
            if dev_id:
                devs[dev_id] = rec
                seen_slugs.add(slug)
        except Exception:
            pass
    print(f"Załadowano {len(devs)} rekordów deweloperów.")

    section_a(devs, min_score)
    section_b(devs)


if __name__ == "__main__":
    main()
