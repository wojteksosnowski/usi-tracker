from pathlib import Path
from python_worker.detect_similar_invs import detect_similar_invs
import logging

logging.basicConfig(level=logging.DEBUG)
detect_similar_invs(Path("/Volumes/Samsam/claude-py/usi-tracker/Public/USIdata"), target_dev_slug="4estates")
