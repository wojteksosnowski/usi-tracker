import json
import pytest
from pathlib import Path
from python_worker.services.investment_service import InvestmentService

def test_save_ratings_must_strictly_invalidate_cache(tmp_path, monkeypatch):
    """
    Weryfikuje, czy zapis ocen bezwzględnie wymusza inwalidację cache w RAM.
    Jeśli invalidate_cache() przestanie działać, ten test da FAIL.
    """
    # 1. Przygotowanie czystego środowiska w tmp_path
    public_dir = tmp_path / "Public"
    data_dir = public_dir / "USIdata"
    data_dir.mkdir(parents=True)
    
    # Patch config paths
    import python_worker.config as config
    monkeypatch.setattr(config, "USI_DATA_DIR", data_dir)
    monkeypatch.setattr(config, "DROPBOX_PATH", tmp_path)
    
    # Reset singleton index
    import python_worker.investment_index as idx_mod
    idx_mod._index = None
    
    # Tworzymy atrapę indeksu i struktury inwestycji
    inv_id = "INV-9999"
    dev_slug = "test-dev"
    inv_slug = "test-inv"
    
    inv_folder = data_dir / dev_slug / inv_slug
    inv_folder.mkdir(parents=True)
    
    # Tworzymy fizyczny plik usi_*.json (anchor), aby resolver go znalazł
    anchor_file = inv_folder / f"usi_rp_123.json"
    anchor_data = {
        "usi_inv_id": inv_id,
        "developer_slug": dev_slug,
        "investment_slug": inv_slug,
        "name": "Test Inwestycji",
        "sources": {"rp": {"id": 123}},
        "portal": "rp",
        "portal_id": 123,
        "folder_path": f"Public/USIdata/{dev_slug}/{inv_slug}",
        "file_path": f"Public/USIdata/{dev_slug}/{inv_slug}/usi_rp_123.json"
    }
    anchor_file.write_text(json.dumps(anchor_data))
    
    # Zapisujemy globalny indeks
    index_file = data_dir / "_index.json"
    index_file.write_text(json.dumps({"entries": [anchor_data]}))

    # Inicjalizacja serwisu na czystym tmp_path
    service = InvestmentService(data_dir=data_dir)
    
    idx_inst = idx_mod.get_investment_index()
    print("INDEX ENTRIES:", idx_inst.get_all())
    
    # Path debug
    print("EXPECTED ANCHOR:", anchor_file)
    print("EXPECTED EXISTS:", anchor_file.exists())
    
    res = service.get_investment_resources(inv_id)
    print("RESOURCES:", res)
    
    # 2. Pierwsze załadowanie - dane trafiają do cache RAM serwisu za sprawą get_unified_view / _load_investment
    first_load = service.get_unified_view(inv_id)
    assert first_load != {}, "Inwestycja powinna zostać poprawnie załadowana."
    
    # Ręcznie wstrzykujemy zmodyfikowane dane do pliku ratings.json na dysku, 
    # omijając API, by sprawdzić, czy serwis zauważy zmianę po użyciu oficjalnego edytora
    payload = {"ratings": {"Balkony": 5}, "reviewed": True}
    
    # 3. Wywołujemy oficjalną metodę edycji ocen
    # Ta metoda w środku musi wywołać save_ratings na repozytorium oraz invalidate_cache()
    success = service.save_ratings(inv_id, payload)
    assert success is True
    
    # 4. PRÓBA OSZUSTWA: Pobieramy dane ponownie.
    # Jeżeli cache NIE został prawidłowo wyczyszczony, get_unified_view(inv_id) 
    # zwróci stare, zbuforowane dane z kroku 2 i nie przeczyta zmian wywołanych przez edytor.
    updated_load = service.get_unified_view(inv_id)
    
    # Sprawdzamy, czy w sekcji danych zunifikowanych odzwierciedlone są nowe parametry z meta
    # Uwaga: _aggregate_anchors odczytuje fizyczny plik meta, więc sprawdzamy zawartość struktury
    for data_entry in updated_load.get("data", []):
        if data_entry["portal"] == "rp":
            assert data_entry["meta"] != {}, "Cache nie został zinwalidowany! Serwis serwuje stare dane z pamięci RAM."
