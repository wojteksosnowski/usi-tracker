import sys
import logging
sys.path.append("/Volumes/Samsam/claude-py/usi-tracker")
from python_worker.services.investment_sync import get_shared_sync_service

logging.basicConfig(level=logging.INFO)

svc = get_shared_sync_service()
dev_slug, inv_slug, usi_inv_id, data, path = svc.register_investment(
    portal="oto",
    developer_name="Nowa Deweloper",
    name="nowa-czestochowa-malopolska",
    item_id="4BFOJ",
    url="https://www.otodom.pl/pl/oferta/nowa-czestochowa-malopolska-ID4BFOJ",
    allow_existing=True
)

print(f"usi_inv_id: {usi_inv_id}")
print(f"data sources: {data.get('sources')}")
