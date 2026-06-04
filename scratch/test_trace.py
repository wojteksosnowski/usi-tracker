import logging
from pathlib import Path
from python_worker.config import get_scraper_config, USI_DATA_DIR
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.services.investment_sync import InvestmentSyncService

data_dir = Path(USI_DATA_DIR)
public_dir = data_dir.parent / "USI"
resolver = InvestmentIdentityResolver(data_dir, public_dir)
svc = InvestmentSyncService(resolver, data_dir, public_dir)

investments = [{"id": "17702", "url": "https://rynekpierwotny.pl/test", "vendor_id": "1084", "developer_name": "Atal"}]

targets, _ = svc._prepare_batch_identifiers("rp", investments)
print("TYPE OF IDENT:", type(targets[0]["identifier"]))
print("IDENT:", targets[0]["identifier"])
