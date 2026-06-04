from pathlib import Path
from python_worker.services.investment_sync import InvestmentSyncService

class MockDM:
    def get_existing_identifiers(self):
        return {
            "rp_ids": {"123", "456"},
            "oto_ids": {"789", "hash123"},
            "to_ids": {"321"},
            "oto_slugs": {"stare-osiedle"}
        }

class MockRepo:
    pass

class MockIdentity:
    pass

svc = InvestmentSyncService(MockIdentity(), Path("/tmp"), Path("/tmp"), developer_manager=MockDM(), investment_repo=MockRepo())
print("RP existing:", svc._check_investment_exists("rp", "123", "slug", "url"))
print("RP missing:", svc._check_investment_exists("rp", "999", "slug", "url"))
print("OTO existing ID:", svc._check_investment_exists("oto", "789", "slug", "url"))
print("OTO missing ID, existing hash in slug:", svc._check_investment_exists("oto", "999", "nowe-osiedle-IDhash123", "url"))
print("OTO missing ID, existing hash in url:", svc._check_investment_exists("oto", "999", "slug", "http://oto.pl/oferta-IDhash123"))
print("OTO existing slug (should be False now!):", svc._check_investment_exists("oto", "999", "stare-osiedle", "url"))
print("TO existing:", svc._check_investment_exists("to", "321", "slug", "url"))
