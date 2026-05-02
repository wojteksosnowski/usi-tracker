import logging
from datetime import datetime
from .config import USI_DATA_DIR

def log_to_processing_log(dev_slug, inv_slug, message):
    """Appends a message to the investment's processing_log_{slug}.txt with timestamp and slug."""
    inv_dir = USI_DATA_DIR / dev_slug / inv_slug
    inv_dir.mkdir(parents=True, exist_ok=True)
    log_path = inv_dir / f"processing_log_{inv_slug}.txt"
    ts = datetime.now().isoformat()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {dev_slug}/{inv_slug} - {message}\n")
