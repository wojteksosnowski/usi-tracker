#!/bin/bash
# USI Tracker — uruchamia interfejs webowy i otwiera przeglądarkę
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PORT=5000

# Czyszczenie zablokowanego portu
lsof -ti :$PORT | xargs kill -9 2>/dev/null || true

# Utwórz / odśwież venv jeśli brakuje flask
if [ ! -f "$VENV/bin/python3" ]; then
  echo "→ Tworzę środowisko wirtualne..."
  /opt/homebrew/bin/python3 -m venv "$VENV"
fi

if ! "$VENV/bin/python3" -c "import flask" 2>/dev/null; then
  echo "→ Instaluję zależności..."
  "$VENV/bin/pip" install -q -r "$SCRIPT_DIR/python_worker/requirements.txt"
fi

# Otwórz przeglądarkę po chwili (zanim serwer się podniesie)
(sleep 1 && open "http://localhost:$PORT") &

echo "→ USI Tracker UI: http://localhost:$PORT"
echo "   Ctrl+C aby zatrzymać"
echo ""

mkdir -p "$SCRIPT_DIR/logs"
cd "$SCRIPT_DIR"
exec "$VENV/bin/python3" -m python_worker.main ui
