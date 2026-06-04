import logging
from pathlib import Path
from python_worker.config import get_scraper_config, USI_DATA_DIR
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.services.investment_sync import InvestmentSyncService

logging.basicConfig(level=logging.INFO)

data_dir = Path(USI_DATA_DIR)
public_dir = data_dir.parent / "USI"
resolver = InvestmentIdentityResolver(data_dir, public_dir)
svc = InvestmentSyncService(resolver, data_dir, public_dir)

investments = [
    {
        "id": "17702",
        "url": "https://rynekpierwotny.pl/test",
        "vendor_id": "1084",
        "developer_name": "Atal"
    }
]

import usi_scrapers.api as api
original_process_batch = api.process_batch

def mocked_process_batch(config, fetcher, portal, targets, *args, **kwargs):
    print("MOCKED process_batch received targets:")
    print(targets)
    for t in targets:
        print("MOCKED identifier:", t.get("identifier"), type(t.get("identifier")))
    return original_process_batch(config, fetcher, portal, targets, *args, **kwargs)

api.process_batch = mocked_process_batch

try:
    svc.process_batch("rp", investments)
except Exception as e:
    print(f"FAILED: {e}")
