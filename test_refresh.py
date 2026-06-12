import logging
logging.basicConfig(level=logging.INFO)

from python_worker.services.investment_sync import InvestmentSyncService
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

identity = InvestmentIdentityResolver(data_dir=USI_DATA_DIR, public_usi_dir=PUBLIC_USI_DIR)
sync = InvestmentSyncService(identity_resolver=identity, data_dir=USI_DATA_DIR, public_usi_dir=PUBLIC_USI_DIR)
result = sync.update_investment("oto_4vrJI")
print(f"Update Result: {result}")
