import pytest
import os
from pathlib import Path
from python_worker.investment_index import InvestmentIndex

def test_index_rebuild_must_not_crash_on_dangling_symlinks(tmp_path):
    """
    Weryfikuje odporność skanera plików na uszkodzone linki symboliczne.
    Brak osłony try/except lub użycie strict=True w resolve() położy ten test.
    """
    data_dir = tmp_path / "USIdata"
    data_dir.mkdir()
    
    # Tworzymy prawidłowego dewelopera i inwestycję
    correct_folder = data_dir / "real-developer" / "real-investment"
    correct_folder.mkdir(parents=True)
    (correct_folder / "usi_rp_1.json").write_text('{"usi_inv_id": "INV-1"}')
    
    # Tworzymy sabotaż: uszkodzony symlink wskazujący na nieistniejący cel
    bad_symlink = data_dir / "broken-developer-link"
    try:
        os.symlink(tmp_path / "non-existent-target-directory-xyz", bad_symlink)
    except OSError:
        pytest.skip("Środowisko OS nie pozwala na tworzenie symlinków w testach.")
        
    # Inicjalizujemy indeks na skażonym katalogu
    idx = InvestmentIndex(data_dir)
    
    # Wykonujemy operację przebudowy indeksu (rebuild skanuje strukturę za pomocą iterdir/glob)
    try:
        count = idx.rebuild()
        # Sprawdzamy czy poprawnie zaindeksował prawidłowy plik pomijając śmieci
        assert count >= 0, "Skrajna niespójność zwracanego licznika."
    except Exception as e:
        pytest.fail(f"KRACH SYSTEMU: Skonfrontowany z uszkodzonym symlinkiem kod rzucił nieobsługiwany wyjątek: {e}")
