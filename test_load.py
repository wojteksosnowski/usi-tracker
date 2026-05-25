import time
from pathlib import Path
from python_worker.api.utils import _load_investment

data_dir = Path("Public/USIdata")
public_usi_dir = Path("Public/USI")
start = time.time()
count = 0
for dev_dir in data_dir.iterdir():
    if not dev_dir.is_dir() or dev_dir.name.startswith("."): continue
    for inv_dir in dev_dir.iterdir():
        if not inv_dir.is_dir() or inv_dir.name.startswith("."): continue
        count += 1
        if count > 100: break
    if count > 100: break

start = time.time()
for dev_dir in data_dir.iterdir():
    if not dev_dir.is_dir() or dev_dir.name.startswith("."): continue
    for inv_dir in dev_dir.iterdir():
        if not inv_dir.is_dir() or inv_dir.name.startswith("."): continue
        _load_investment(dev_dir.name, inv_dir.name, data_dir=data_dir, public_usi_dir=public_usi_dir)
        count -= 1
        if count <= 0: break
    if count <= 0: break

print(f"Time for 100 items: {time.time() - start:.2f}s")
