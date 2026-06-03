#!/bin/bash

# Przejście do katalogu projektu
cd "$(dirname "$0")"

echo "=== Rozpoczynam masową aktualizację inwestycji RynekPierwotny ==="

# Aktywacja środowiska wirtualnego
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Błąd: Nie znaleziono venv/bin/activate!"
    exit 1
fi

# Uruchomienie zoptymalizowanego skryptu Pythona
python3 -m python_worker.mass_update_rp

echo "=== Gotowe! ==="
