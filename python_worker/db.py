"""
db.py — Czysty, radykalnie uproszczony dostęp do danych inwestycji.

Zasada: Merger wykonał swoją robotę i zapisał gotowy JSON na dysk.
Loader czyta i zwraca. Zero klas, zero GOF, zero parsowania stringów.

Indeks (_index.json) mapuje: system_id → file_path (względna od DROPBOX_PATH).
"""
import json
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any

from python_worker.config import USI_DATA_DIR, DROPBOX_PATH

logger = logging.getLogger(__name__)

_INDEX_PATH = Path(USI_DATA_DIR) / "_index.json"
_BASE_PATH = DROPBOX_PATH


def _read_index() -> dict:
    """Odczytuje _index.json jako dict[id → entry]."""
    if not _INDEX_PATH.exists():
        logger.error("Globalny indeks _index.json nie istnieje. Uruchom rebuild-index.")
        return {}
    try:
        return json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Uszkodzony indeks _index.json: {e}")
        return {}


def load_investment(system_id: str) -> Optional[Dict[str, Any]]:
    """
    Radykalnie uproszczony loader inwestycji.
    1. Sprawdza file_path w _index.json (O(1) lookup).
    2. Odczytuje plik JSON z dysku.
    3. Zwraca gotowy słownik bezpośrednio do API/UI.

    Zero agregacji w locie, zero parsowania stringów.
    Merger ma obowiązek zapisać czysty, kompletny JSON.
    """
    if not system_id:
        return None

    index = _read_index()
    entry = index.get("entries_map", {}).get(system_id)

    if not entry or not entry.get("file_path"):
        logger.warning(f"ID {system_id} nie istnieje w indeksie lub brak file_path.")
        return None

    file_path = _BASE_PATH / entry["file_path"]
    if not file_path.exists():
        logger.error(f"Plik JSON nie istnieje na dysku: {file_path}")
        return None

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Uszkodzony plik JSON dla {system_id}: {e}")
        return None


def save_investment(system_id: str, data: Dict[str, Any]) -> bool:
    """
    Atomowy zapis pliku inwestycji na dysk.
    Używany przez endpointy edycji (oceny, zdjęcia, etc.).
    """
    index = _read_index()
    entry = index.get("entries_map", {}).get(system_id)

    if not entry or not entry.get("file_path"):
        logger.error(f"Nie można zapisać {system_id}: brak file_path w indeksie.")
        return False

    file_path = _BASE_PATH / entry["file_path"]

    try:
        fd, tmp = tempfile.mkstemp(dir=file_path.parent, prefix=".tmp_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, file_path)
            return True
        except Exception:
            os.unlink(tmp)
            raise
    except Exception as e:
        logger.error(f"Atomowy zapis dla {system_id} nie powiódł się: {e}")
        return False
