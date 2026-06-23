import pytest
from pathlib import Path
from python_worker.investment_repository import InvestmentRepository
from python_worker.services.investment_identity import InvestmentIdentityResolver

def test_repository_must_reject_invalid_investment_payload(tmp_path):
    """
    Testuje weryfikację struktury zapisywanego pliku na poziomie repozytorium.
    Zapis pliku inwestycji bez kluczowych pól (np. 'usi_inv_id') musi rzucić wyjątek walidacji (np. ValueError / ValidationError) 
    zamiast zapisać błędny stan na dysk.
    """
    data_dir = tmp_path / "USIdata"
    data_dir.mkdir()
    
    # Tworzymy atrapę folderu
    inv_dir = data_dir / "test-dev" / "test-inv"
    inv_dir.mkdir(parents=True)
    
    identity = InvestmentIdentityResolver(data_dir)
    repo = InvestmentRepository(identity, data_dir)
    
    # Niekompletny payload - brakuje usi_inv_id, developer_slug, itd.
    bad_payload = {
        "name": "Brak ID Inwestycji"
    }
    
    system_id = "rp_123"
    anchor_path = inv_dir / "usi_rp_123.json"
    
    # Oczekujemy, że repozytorium samo obroni się przed zapisem śmieciowych danych
    with pytest.raises(ValueError, match="usi_inv_id"):
        repo.save_investment_json(system_id, bad_payload, anchor_path=anchor_path)
    
    # Upewniamy się, że dysk pozostał czysty
    assert not anchor_path.exists(), "BŁĄD: Repozytorium zapisało uszkodzony plik ignorując walidację schematu!"
