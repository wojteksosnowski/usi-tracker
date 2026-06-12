import sys
from pathlib import Path
from python_worker.developer_manager import DeveloperManager

dm = DeveloperManager(Path("Public/USIdata"))
ids = dm.get_existing_identifiers()
print(f"Is 4BuBt in oto_ids? {'4BuBt' in ids['oto_ids']}")
