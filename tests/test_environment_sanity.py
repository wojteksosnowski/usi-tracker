import os
from pathlib import Path

def test_enforce_reference_data_presence():
    """
    Test bezpiecznikowy. Zapobiega oszukiwaniu przez zielone testy, 
    które po cichu pomijają wykonanie z powodu dekoratorów skipif.
    """
    required_dirs = [
        Path("reference-data/coda"),
        Path("python_worker/data"),
    ]
    
    # Jeśli działasz w środowisku CI, brak tych katalogów to bezwzględny błąd
    if os.getenv("CI") or os.getenv("STRICT_TESTS") == "1":
        for directory in required_dirs:
            assert directory.exists(), f"Krytyczna awaria środowiska testowego: brak katalogu {directory}. Testy byłyby po cichu pomijane!"
