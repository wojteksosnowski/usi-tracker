from pathlib import Path
from python_worker.investment_index import rebuild
print(rebuild(Path("Public/USIdata"), Path("Public/USI")))
