import pytest
import json
from pathlib import Path
from python_worker.daemons import TrackerDoktorDelegate
from python_worker.algorithms.similarity.engine import calculate_similarities
from python_worker.developer_index import rebuild as rebuild_index

def test_suggest_e2e_pipeline(tmp_path: Path):
    """
    E2E Test dla systemu sugestii.
    Weryfikuje cały rurociąg działający w ramach komendy 'suggest': 
    1. Odczyt fizycznych plików poprzez hot index (zależność od I/O).
    2. Obliczenie prawdopodobieństwa przez silnik (mock data flow).
    3. Zapis sugestii z powrotem na dysk poprzez TrackerDoktorDelegate.
    """
    dev_dir = tmp_path / "USIdev"
    inv_dir = tmp_path / "USIdata"
    dev_dir.mkdir(parents=True)
    inv_dir.mkdir(parents=True)
    
    # Utworzenie referencyjnego dewelopera
    dev1_slug = "dev-1-slug"
    dev1_dir = dev_dir / dev1_slug
    dev1_dir.mkdir()
    
    dev1_data = {
        "developer_slug": dev1_slug,
        "name": "Super Development",
        "usi_dev_id": "DEV-E2E-001",
        "portal_mapping": {"rp": {"id": "1", "slug": dev1_slug}, "oto": None, "to": None},
        "investments": [{"slug": "dev-1-slug/inv-1"}]
    }
    
    with open(dev1_dir / "usi_dev_rp_1.json", "w", encoding="utf-8") as f:
        json.dump(dev1_data, f)
        
    # Utworzenie identycznego dewelopera do sparowania
    dev2_slug = "super-development-sp-z-o-o"
    dev2_dir = dev_dir / dev2_slug
    dev2_dir.mkdir()
    
    dev2_data = {
        "developer_slug": dev2_slug,
        "name": "Super Development Sp. z o.o.",
        "usi_dev_id": "DEV-E2E-002",
        "portal_mapping": {"rp": None, "oto": {"agency_id": "2", "agency_ids": ["2"]}, "to": None},
        "investments": [{"slug": "super-development-sp-z-o-o/inv-2"}]
    }
    
    with open(dev2_dir / "usi_dev_oto_2.json", "w", encoding="utf-8") as f:
        json.dump(dev2_data, f)
        
    # Symulacja: Odbudowa gorącego indeksu na podstawie plików dyskowych
    rebuild_index(inv_dir, dev_dir)
    
    # Inicjalizacja delegata operującego na naszym tymczasowym systemie plików
    delegate = TrackerDoktorDelegate(inv_dir, dev_dir)
    
    # Krok 1: Wczytanie z indeksu (I/O)
    devs = delegate.get_developers_for_analysis()
    assert len(devs) == 2, "Delegate nie pobrał wszystkich deweloperów z dysku/indeksu."
    
    # Krok 2: Algorytm podobieństwa
    dismissed = delegate.get_dismissed_cache()
    suggestions = calculate_similarities(devs, dismissed)
    
    # Zabezpieczenie testu - upewniamy się, że znaleziono relację
    assert len(suggestions) > 0, "Brak znalezionych podobieństw w ogóle."
    has_match = any(
        s["source_id"] == "DEV-E2E-001" and s["target_id"] == "DEV-E2E-002"
        for s in suggestions
    )
    assert has_match, "Algorytm nie dopasował dwóch bliźniaczych deweloperów."
    
    # Krok 3: Symulacja agregacji wyciągnięta wprost z komendy `suggest`
    unique_suggestions = {}
    for s in suggestions:
        key = (s["source_id"], s["target_id"])
        if key not in unique_suggestions or s["score"] > unique_suggestions[key]["score"]:
            unique_suggestions[key] = s
            
    grouped = {}
    for s in unique_suggestions.values():
        grouped.setdefault(s["source_id"], []).append({
            "target_id": s["target_id"],
            "target_slug": s["target_slug"],
            "reason": s["reason"],
            "score": s["score"]
        })
        
    # Krok 4: Zapis wyników do plików (Testujemy ścieżkę I/O)
    for dev_id, sugs in grouped.items():
        delegate.save_suggestions(dev_id, sugs)
        
    # Krok 5: Weryfikacja pliku po modyfikacji (via get_developer_by_id which reads master file)
    dev1_updated = delegate.dm.get_developer_by_id("DEV-E2E-001")
        
    assert "suggestions" in dev1_updated, "Brak pola 'suggestions' po zapisie."
    saved_suggestions = dev1_updated["suggestions"]
    assert len(saved_suggestions) > 0, "Lista sugestii została zapisana jako pusta."
    
    # Weryfikacja dokładnej struktury obiektu zapisanego do pliku JSON
    saved_target = saved_suggestions[0]["usi_dev_id"]
    assert saved_target == "DEV-E2E-002", f"Oczekiwano DEV-E2E-002, znaleziono {saved_target}"
    assert "reason" in saved_suggestions[0], "Zapis zgubił pole 'reason' podczas serializacji."
    assert "score" in saved_suggestions[0], "Zapis zgubił pole 'score' podczas serializacji."
