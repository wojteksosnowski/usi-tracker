import pytest
from pathlib import Path
from python_worker.services.investment_service import InvestmentService

def test_registration_must_fail_to_unknown_folder_when_id_matching_is_absent(tmp_path, monkeypatch):
    """
    Wymusza przestrzeganie zasady ID-only. Jeśli system spróbuje heurystycznie 
    dopasować dewelopera po nazwie tekstowej, zamiast wrzucić do 'unknown', test ma spaść.
    """
    public_dir = tmp_path / "Public"
    data_dir = public_dir / "USIdata"
    data_dir.mkdir(parents=True)
    
    import python_worker.config as config
    monkeypatch.setattr(config, "USI_DATA_DIR", data_dir)
    monkeypatch.setattr(config, "DROPBOX_PATH", tmp_path)
    monkeypatch.setattr(config, "PUBLIC_USI_DIR", public_dir / "USI")
    
    import python_worker.investment_index as idx_mod
    idx_mod._index = None
    
    from python_worker.services.scraper_gateway import ScraperGateway
    
    def fake_refresh(*args, **kwargs):
        # Symulujemy pomyślne pobranie payloadu, żeby przejść do logiki mapowania ścieżki
        import json
        inv_dir = data_dir / "unknown" / "inv-99999"
        inv_dir.mkdir(parents=True, exist_ok=True)
        (inv_dir / "raw_rp_99999.json").write_text(json.dumps({"id": 99999, "name": "Apartamenty Widmo"}))
        
        return {
            "id": 99999,
            "name": "Apartamenty Widmo",
            "url": "https://rynekpierwotny.pl/oferty/widmo-dev/apartamenty-widmo-99999/",
            "developer_name": "Istniejący Tekstowo Deweloper S.A.",
            "vendor_id": 88888,
            "raw_details": {"id": 99999, "name": "Apartamenty Widmo"}
        }
    monkeypatch.setattr(ScraperGateway, "refresh_investment_by_id", fake_refresh)
    monkeypatch.setattr(ScraperGateway, "ingest_investment_by_url", fake_refresh)
    
    service = InvestmentService(data_dir=data_dir)
    
    # Symulujemy payload inwestycji z nazwą dewelopera, którego nie ma w bazie ID portalu
    payload = {
        "id": "99999",
        "name": "Apartamenty Widmo",
        "url": "https://rynekpierwotny.pl/oferty/widmo-dev/apartamenty-widmo-99999/",
        "developer_name": "Istniejący Tekstowo Deweloper S.A.", # Nazwa jest, ale brak mapowania ID
        "vendor_id": 88888
    }
    
    # Wywołujemy rejestrację inwestycji
    result = service.register_investment(portal="rp", payload=payload)
    
    # Oczekujemy, że rejestracja rzuci wyjątek lub przypisze inwestycję do folderu 'unknown'
    # Weryfikujemy sztywny kontrakt biznesowy: brak dopasowania ID = folder "unknown"
    assert result["ok"] is True, f"Rejestracja zwróciła błąd: {result.get('error')}"
    assert "unknown/" in result["slug"], "ZŁAMANIE ARCHITEKTURY: Inwestycja została przypisana do dewelopera na podstawie nazwy tekstowej, a nie twardego ID portalowego!"
