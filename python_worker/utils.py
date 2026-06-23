import json
import os
import tempfile
from pathlib import Path
import logging

def write_json_atomically(file_path: Path, data: dict, indent: int = 2) -> bool:
    """Zapewnia atomowy i bezpieczny zapis pliku JSON na dysku."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=file_path.parent, prefix=".tmp_", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            os.replace(tmp_path, file_path)
            return True
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    except Exception as e:
        logging.getLogger("USIWorker.Utils").error(f"Atomic write failed for {file_path}: {e}")
        return False
