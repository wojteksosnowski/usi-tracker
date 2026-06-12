#!/bin/bash
# USI Tracker — odbudowuje index inwestycji i generuje sugestie duplikatów deweloperów
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PY="$VENV/bin/python3"

if [ ! -f "$PY" ]; then
  echo "Brak venv — uruchom najpierw: python3 -m venv venv && venv/bin/pip install -r python_worker/requirements.txt"
  exit 1
fi

cd "$SCRIPT_DIR"

echo "→ Odbudowuję index deweloperów (wymagane dla wydajności)..."
"$PY" -m python_worker.main rebuild-dev-index

echo "→ Odbudowuję index inwestycji..."
"$PY" -m python_worker.main rebuild-index

echo ""
echo "Gotowe."
