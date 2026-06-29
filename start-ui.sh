#!/bin/bash
# USI Tracker — uruchamia interfejs webowy i otwiera przeglądarkę
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PORT=5000

# Analiza argumentów wejściowych
UPDATE_DEPS=false
REBUILD_INDEX=false

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --update) UPDATE_DEPS=true ;;
    --index) REBUILD_INDEX=true ;;
    *) echo "Nieznana opcja: $1"; exit 1 ;;
  esac
  shift
done

# Czyszczenie zablokowanego portu
lsof -ti :$PORT | xargs kill -9 2>/dev/null || true

# Utwórz / odśwież venv jeśli brakuje flask
if [ ! -f "$VENV/bin/python3" ]; then
  echo "→ Tworzę środowisko wirtualne..."
  /opt/homebrew/bin/python3 -m venv "$VENV"
fi

# Filtrowanie requirements.txt w locie (wykluczamy usi-scrapers z PyPI)
install_requirements() {
  local pip_cmd="$1"
  local extra_flags="$2"
  grep -v "usi-scrapers" "$SCRIPT_DIR/python_worker/requirements.txt" | "$VENV/bin/pip" install $extra_flags -r /dev/stdin
}

if $UPDATE_DEPS; then
  echo "→ Aktualizuję wszystkie dependencies w środowisku wirtualnym..."
  install_requirements "$VENV/bin/pip" "--upgrade"
  if [ -d "$SCRIPT_DIR/../usi-scrapers" ]; then
    echo "→ Instaluję lokalny pakiet usi-scrapers w trybie edycji..."
    "$VENV/bin/pip" install -e "$SCRIPT_DIR/../usi-scrapers"
  else
    echo "⚠️ Ostrzeżenie: Katalog ../usi-scrapers nie istnieje. Pomijam aktualizację usi-scrapers."
  fi
elif ! "$VENV/bin/python3" -c "import flask" 2>/dev/null; then
  echo "→ Instaluję brakujące zależności..."
  install_requirements "$VENV/bin/pip" "-q"
  if [ -d "$SCRIPT_DIR/../usi-scrapers" ]; then
    "$VENV/bin/pip" install -e "$SCRIPT_DIR/../usi-scrapers"
  fi
fi

if $REBUILD_INDEX; then
  echo "→ Aktualizuję indeksy..."
  "$VENV/bin/python3" -m python_worker.main rebuild-dev-index
  "$VENV/bin/python3" -m python_worker.main rebuild-index
fi

# Otwórz przeglądarkę po chwili (zanim serwer się podniesie)
(sleep 1 && open "http://localhost:$PORT") &

echo "→ USI Tracker UI: http://localhost:$PORT"
echo "   Ctrl+C aby zatrzymać"
echo ""

mkdir -p "$SCRIPT_DIR/logs"
cd "$SCRIPT_DIR"
exec "$VENV/bin/python3" -m python_worker.main ui
