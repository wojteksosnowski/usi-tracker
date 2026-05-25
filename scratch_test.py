import sys
from pathlib import Path
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR

dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
dev = dm.get_developer_by_id("DEV-26080")
print(dev.get("is_child"))
print(dev.get("developer_slug"))
