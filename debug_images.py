import json
from pathlib import Path
from python_worker.api.utils import _load_investment
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

dev_slug = "madey-development-sp-z-o-o-4-sp-k"
inv_slug = "cascada-lodz-julianow-marysin-rogi"

print(f"Data Dir: {USI_DATA_DIR}")
print(f"Public USI Dir: {PUBLIC_USI_DIR}")

res = _load_investment(dev_slug, inv_slug)
if res:
    print(f"Name: {res['name']}")
    print(f"Photos: {res['photos']}")
else:
    print("Investment not found")
