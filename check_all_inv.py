from python_worker.services.investment_service import InvestmentService
from python_worker.config import USI_DATA_DIR
from pathlib import Path

isvc = InvestmentService()
data_root = Path(USI_DATA_DIR)

found = False
for dev_dir in sorted(data_root.iterdir()):
    if not dev_dir.is_dir(): continue
    for inv_dir in sorted(dev_dir.iterdir()):
        if not inv_dir.is_dir(): continue
        if "cascada" in inv_dir.name:
            inv = isvc.get_investment(dev_dir.name, inv_dir.name)
            print(f"Investment: {inv['slug']}")
            print(f"Developer: {inv['developer']}")
            print(f"Photos count: {len(inv['photos'])}")
            print(f"Photos: {inv['photos']}")
            found = True

if not found:
    print("Cascada not found in database")
