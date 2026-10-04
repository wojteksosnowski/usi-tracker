"""Kolejka nieskategoryzowanych udogodnień.

Liczy, w iluu masterach występuje każda etykieta, której katalog kanoniczny
(data/amenity_catalog.json) nie rozpoznaje, i zapisuje data/amenity_unmatched.json
(malejąco po n). Do triażu: dopisz alias do pojęcia albo wzorzec do `noise`
w scripts/build_amenity_catalog.py i uruchom go ponownie.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.investment_index import InvestmentIndex
from python_worker.services.amenity_normalizer import canonicalize
from python_worker.services.investment_loader import InvestmentLoaderService

OUT_PATH = Path(__file__).parent / "data" / "amenity_unmatched.json"


def update_amenities_freq():
    idx = InvestmentIndex()
    loader = InvestmentLoaderService()
    counts, examples = Counter(), {}

    all_invs = idx.get_all()
    total = len(all_invs)
    print(f"Loaded {total} master investments from index.")

    for i, inv in enumerate(all_invs):
        if i % 1000 == 0:
            print(f"Processed {i}/{total}...")
        full_inv = loader.load_investment(inv["id"])
        if not full_inv:
            continue
        amenities = full_inv.get("amenities", [])
        labels = amenities.get("labels", []) if isinstance(amenities, dict) else (amenities or [])
        for tag in canonicalize(labels)["unmatched"]:
            counts[tag] += 1
            examples.setdefault(tag, inv["id"])

    rows = [{"label": t, "n": n, "example": examples[t]} for t, n in counts.most_common()]
    OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Zapisano {len(rows)} nieskategoryzowanych etykiet do {OUT_PATH}")


if __name__ == "__main__":
    update_amenities_freq()
