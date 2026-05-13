import json
import pytest
from pathlib import Path
from python_worker.csv_importer import (
    extract_ratings, extract_native_slugs, build_rp_result, build_oto_result
)
from python_worker.adapters import RPAdapter, OtodomAdapter, Merger

def test_split_dual_record_parity():
    # Dane testowe: rekord dualny (RP + OTO)
    row = {
        "USIfolder": "hybrid-investment",
        "Deweloper": "Test Developer",
        "imgList": "/Public/USI/test-dev-old/test-inv-old/1.jpg, /Public/USI/test-dev-old/test-inv-old/2.jpg",
        "Ocena": "Dobra",
        "Gwiazdki": "★★★",
        "Balkony": "4.5",
        "Wnętrza": "3.0",
        "rpJSON": json.dumps({"slug": "native-rp-slug", "name": "RP Name", "properties": 100}),
        "otoJSON": json.dumps({"ad": {"title": "OTO Title", "location": {"mapDetails": {"lat": 52.1, "lon": 21.0}}}})
    }

    # 1. Ekstrakcja ocen
    ratings = extract_ratings(row)
    assert ratings["Gwiazdki"] == 3
    assert ratings["Balkony"] == 4.5

    # 2. Rozdzielenie slugów
    rp_slug, oto_slug = extract_native_slugs(row)
    assert rp_slug == "native-rp-slug"
    assert oto_slug == "hybrid-investment" # Fallback bo brak linku OTO w row

    # 3. Budowanie wyników pośrednich (app_result)
    rp_res = build_rp_result(row, investment_slug=rp_slug, ratings=ratings)
    oto_res = build_oto_result(row, investment_slug=oto_slug, ratings=ratings)

    # 4. WERYFIKACJA ŚCIEŻEK (Read-Only USI/)
    # Muszą wskazywać na STARY folder z imgList, a nie na nowo wygenerowane slugi
    assert rp_res["usi_folder_path"] == "/Public/USI/test-dev-old/test-inv-old/"
    assert oto_res["usi_folder_path"] == "/Public/USI/test-dev-old/test-inv-old/"
    assert "/Public/USI/test-dev-old/test-inv-old/1.jpg" in rp_res["image_paths"]
    assert "/Public/USI/test-dev-old/test-inv-old/2.jpg" in oto_res["image_paths"]

    # 5. TRANSFORMACJA PRZEZ ADAPTERY (usi-scrapers mode)
    rp_unified = RPAdapter.transform(json.loads(row["rpJSON"]), rp_slug, rp_res["developer_slug"])
    oto_unified = OtodomAdapter.transform(json.loads(row["otoJSON"]), oto_slug, oto_res["developer_slug"])

    # INJECT PRESERVED IMAGE DATA (Simulation of new csv_importer logic)
    rp_unified["image_paths"] = rp_res["image_paths"]
    rp_unified["images_count"] = rp_res["images_count"]
    oto_unified["image_paths"] = oto_res["image_paths"]
    oto_unified["images_count"] = oto_res["images_count"]

    # 6. MERGE Z OCENAMI
    final_rp = Merger.merge(rp_data=rp_unified, meta_ratings=ratings)
    final_oto = Merger.merge(oto_data=oto_unified, meta_ratings=ratings)

    # 7. WERYFIKACJA FINALNYCH JSONÓW (Parity Check)
    # Sprawdzamy czy oceny przechodzą przez mergera
    assert final_rp["ratings"]["Balkony"] == 4.5
    assert final_oto["ratings"]["Wnętrza"] == 3.0
    
    # Sprawdzamy czy source jest poprawny
    assert final_rp["sources"]["rp"] is not None
    assert final_oto["sources"]["oto"] is not None
    
    print("\n[OK] Test porównawczy zakończony sukcesem.")
    print(f"RP Image Paths Count: {len(final_rp['image_paths'])}")
    print(f"OTO Image Paths Count: {len(final_oto['image_paths'])}")
    assert final_rp["image_paths"] == rp_res["image_paths"]
    assert final_oto["image_paths"] == oto_res["image_paths"]
