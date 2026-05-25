import json
import logging
from datetime import datetime
from pathlib import Path
from python_worker.config import HERE_API_KEY, SEGMENTS_CONFIG_PATH

logger = logging.getLogger(__name__)

def get_ui_config():
    """Returns centralized UI configuration."""
    config = {
        "hereApiKey": HERE_API_KEY,
        "segments": []
    }
    
    # Load segments from config file
    if SEGMENTS_CONFIG_PATH.exists():
        try:
            with open(SEGMENTS_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                config["segments"] = data.get("segments", [])
        except Exception as e:
            logger.error(f"Failed to load segments for UI config: {e}")
            
    return config

def log_ui_error_to_file(payload):
    """Logs frontend errors to a dedicated log file."""
    msg = payload.get("message", "Unknown error")
    stack = payload.get("stack", "No stack trace")
    url = payload.get("url", "Unknown URL")
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "ui_errors.log"
    
    ts = datetime.now().isoformat()
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"--- UI ERROR at {ts} ---\n")
            f.write(f"URL: {url}\n")
            f.write(f"Message: {msg}\n")
            f.write(f"Stack:\n{stack}\n")
            f.write("-" * 40 + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to write UI error log: {e}")
        return False
